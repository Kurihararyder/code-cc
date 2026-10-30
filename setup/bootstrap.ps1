<#
CPE 教練 安裝程式（Windows）。在檔案總管裡雙擊 install-windows.bat 就會執行這個檔案。
  做的事：找 Python 3.9 以上（沒有就自動安裝）→ 啟動安裝精靈（有圖形畫面用圖形，否則文字模式）。
  -CheckOnly   只檢查，不安裝任何東西、不改任何設定
  -Yes         全部不詢問：缺 Python 時直接自動安裝，安裝精靈也用預設值（不開視窗）
  其他參數（例如 --text、--dir 路徑）原樣交給安裝精靈
#>
[CmdletBinding()]
param(
    [switch]$CheckOnly,
    [switch]$Yes,
    [string]$Repo = $(if ($env:CPE_REPO_SLUG) { $env:CPE_REPO_SLUG } else { "Kurihararyder/code-cc" }),
    [string]$Branch = $(if ($env:CPE_INSTALL_BRANCH) { $env:CPE_INSTALL_BRANCH } else { "claude/clever-archimedes-ekcn2m" }),
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Rest
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

# python.org 的 3.12.10 安裝程式（沒有 winget 時的備案）；雜湊值固定，下載後一定先驗證
$PyInstallers = @{
    "AMD64" = @{ File = "python-3.12.10-amd64.exe"; Sha256 = "67b5635e80ea51072b87941312d00ec8927c4db9ba18938f7ad2d27b328b95fb" }
    "ARM64" = @{ File = "python-3.12.10-arm64.exe"; Sha256 = "377ac8fd478987940088e879441e702a71b53164d2a1e6f1d51ff77a7e470258" }
    "X86"   = @{ File = "python-3.12.10.exe";       Sha256 = "fdfe385b94f5b8785a0226a886979527fd26eb65defdbf29992fd22cc4b0e31e" }
}

function Say($msg) { Write-Host $msg }

function Ask-Yes($question) {
    if ($Yes) { return $true }
    try {
        $a = Read-Host "$question [Y/n]"
    } catch { return $false }
    return ($a -eq "" -or $a -match "^(y|yes|是|好)$")
}

function Refresh-Path {
    $m = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $u = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = (@($m, $u) | Where-Object { $_ }) -join ";"
}

function Test-PythonOk($exe) {
    if (-not $exe -or -not (Test-Path $exe)) { return $false }
    try {
        $v = & $exe -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
        return ($v -and ([version]$v -ge [version]"3.9"))
    } catch { return $false }
}

function Test-Tk($exe) {
    try { & $exe -c "import tkinter" 2>$null | Out-Null; return ($LASTEXITCODE -eq 0) } catch { return $false }
}

# 子程式直接用這個視窗的輸入輸出執行（文字模式要能即時顯示問題、讀你的輸入；不能被 PowerShell 的管線吃掉），回傳結束碼
function Invoke-Native($exe, $arguments) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $exe
    $psi.Arguments = ($arguments | ForEach-Object { if ("$_" -match '\s') { '"' + $_ + '"' } else { "$_" } }) -join " "
    $psi.UseShellExecute = $false          # 不重新導向：直接用這個視窗的輸入輸出。也不用 Start-Process -Wait（它會連子孫程序一起等，圖形精靈開著就不會返回）
    $p = [System.Diagnostics.Process]::Start($psi)
    $p.WaitForExit()
    return $p.ExitCode
}

function Find-Python {
    $cands = New-Object System.Collections.ArrayList
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        try {
            $p = & py -3 -c "import sys; print(sys.executable)" 2>$null
            if ($p) { [void]$cands.Add($p) }
        } catch {}
    }
    foreach ($n in @("python", "python3")) {
        foreach ($c in @(Get-Command $n -All -ErrorAction SilentlyContinue)) {
            # \Microsoft\WindowsApps\python.exe 是會跳出 Microsoft Store 的空殼，不是真正的 Python
            if ($c.Source -and $c.Source -notmatch '\\Microsoft\\WindowsApps\\') { [void]$cands.Add($c.Source) }
        }
    }
    $roots = @("$env:LOCALAPPDATA\Programs\Python", $env:ProgramFiles, ${env:ProgramFiles(x86)})
    foreach ($r in $roots) {
        if ($r -and (Test-Path $r)) {
            Get-ChildItem $r -Directory -Filter "Python3*" -ErrorAction SilentlyContinue | Sort-Object Name -Descending | ForEach-Object {
                [void]$cands.Add((Join-Path $_.FullName "python.exe"))
            }
        }
    }
    $good = @($cands | Select-Object -Unique | Where-Object { Test-PythonOk $_ })
    foreach ($c in $good) { if (Test-Tk $c) { return $c } }     # 優先挑有圖形介面套件的
    if ($good.Count -gt 0) { return $good[0] }
    return $null
}

function Install-Python {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Say "使用 winget 安裝 Python 3.12…（可能要幾分鐘，請不要關閉）"
        & winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements | Out-Host
        if ($LASTEXITCODE -ne 0) {
            & winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements | Out-Host
        }
        Refresh-Path
        if (Find-Python) { return }
        Say "winget 沒有成功，改用 python.org 的安裝程式…"
    }
    $arch = if ($env:PROCESSOR_ARCHITEW6432) { $env:PROCESSOR_ARCHITEW6432 } else { $env:PROCESSOR_ARCHITECTURE }
    $info = $PyInstallers[$arch.ToUpper()]
    if (-not $info) { $info = $PyInstallers["AMD64"] }
    $dir = Join-Path $env:TEMP "cpe-coach-setup"
    New-Item -ItemType Directory -Force $dir | Out-Null
    $exe = Join-Path $dir $info.File
    Say "下載 $($info.File)（約 25 MB）…"
    Invoke-WebRequest -UseBasicParsing -Uri "https://www.python.org/ftp/python/3.12.10/$($info.File)" -OutFile $exe
    $got = (Get-FileHash $exe -Algorithm SHA256).Hash.ToLower()
    if ($got -ne $info.Sha256) {
        Remove-Item $exe -Force -ErrorAction SilentlyContinue
        throw "下載的 Python 安裝程式雜湊值不符（$got），為了安全已中止。請改到 https://www.python.org/downloads/ 手動安裝。"
    }
    Say "雜湊值驗證通過，安裝中…（只裝給目前的使用者，不需要系統管理員）"
    $p = Start-Process -FilePath $exe -ArgumentList "/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_test=0", "Include_doc=0" -Wait -PassThru
    if ($p.ExitCode -ne 0) { throw "Python 安裝程式失敗（代碼 $($p.ExitCode)）" }
    Refresh-Path
}

function Get-Bundle {
    $root = Split-Path -Parent $PSScriptRoot
    if (Test-Path (Join-Path $root "cpe_coach\launcher\__main__.py")) { return $root }
    $url = if ($env:CPE_ARCHIVE_URL) { $env:CPE_ARCHIVE_URL } else { "https://github.com/$Repo/archive/refs/heads/$Branch.zip" }
    $tmp = Join-Path $env:TEMP "cpe-coach-setup\src"
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force $tmp | Out-Null
    Say "下載程式…（$url）"
    Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile (Join-Path $tmp "src.zip")
    Expand-Archive -Path (Join-Path $tmp "src.zip") -DestinationPath (Join-Path $tmp "x") -Force
    $d = Get-ChildItem (Join-Path $tmp "x") -Directory | Select-Object -First 1
    if (-not $d -or -not (Test-Path (Join-Path $d.FullName "cpe_coach\launcher\__main__.py"))) { throw "下載的壓縮檔裡找不到安裝精靈" }
    return $d.FullName
}

function Main {
    Say "== CPE 教練 安裝程式（Windows）"
    $python = Find-Python
    if (-not $python) {
        Say "✗ 找不到 Python 3.9 以上。"
        if ($CheckOnly) {
            $how = if (Get-Command winget -ErrorAction SilentlyContinue) { "winget" } else { "python.org 的安裝程式（雜湊值驗證）" }
            Say "  （檢查模式）正式安裝時會用 $how 自動安裝 Python 3.12。"
            return 0
        }
        if (-not (Ask-Yes "要自動安裝 Python 嗎？（只裝給你自己，不需要系統管理員；約一分鐘）")) {
            Say "已取消。請先安裝 Python（https://www.python.org/downloads/，安裝時勾選 Add python.exe to PATH）後再執行一次。"
            return 1
        }
        Install-Python
        $python = Find-Python
        if (-not $python) { throw "Python 安裝好了但找不到。請登出再登入（或重新開機）後再執行一次。" }
    }
    $ver = & $python -c "import sys; print(sys.version.split()[0])"
    Say "✓ Python：$python（$ver）"
    if (Test-Tk $python) { Say "✓ 圖形介面套件（tkinter）可用" } else { Say "! 這個 Python 沒有 tkinter，安裝精靈會用文字模式。" }

    if ($CheckOnly) {
        $root = Split-Path -Parent $PSScriptRoot
        if (-not (Test-Path (Join-Path $root "cpe_coach\launcher\__main__.py"))) {
            Say "· 這裡沒有程式資料夾；正式安裝時會從 GitHub 下載。"
            return 0
        }
        Say "✓ 程式資料夾：$root"
        Say "== 安裝診斷"
        $env:PYTHONPATH = $root
        return (Invoke-Native $python @("-m", "cpe_coach.launcher", "doctor"))
    }

    $bundle = Get-Bundle
    Say "✓ 程式資料夾：$bundle"
    $argv = @((Join-Path $bundle "cpe-panel.pyw"), "install", "--detach-gui")
    if ($Yes) { $argv += "--yes" }
    if ($Rest) { $argv += $Rest }
    return (Invoke-Native $python $argv)
}

try {
    $rc = Main
    exit ([int]$rc)
} catch {
    Write-Host ("✗ " + $_.Exception.Message)
    exit 1
}
