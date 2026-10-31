// 介面語言與無障礙偏好。目前英文只涵蓋「導覽列」與「學習」頁（洞察／工坊／筆記／目標）的主要文字，其他頁面仍是中文——這是刻意的範圍，不是漏掉。
import { pref } from "./state.js";

const EN = {
  "今日": "Today", "練習": "Practice", "課程": "Course", "考試": "Exam", "學習": "Learn", "統計": "Stats", "設定": "Settings",
  "洞察": "Insights", "工坊": "Workshop", "筆記": "Notes", "目標": "Goal",
  "學習洞察": "Learning insights", "現在該複習": "Due for review now", "未來 14 天的複習量": "Reviews due in the next 14 days", "知識點掌握": "Concept mastery",
  "下一題推薦": "Recommended next", "錯誤本": "Mistake book", "習慣與疲勞": "Habits and fatigue", "成就": "Achievements", "落點預測": "Score forecast", "考試時間策略": "Exam time strategy",
  "考前清單": "Final checklist", "最近 7 天": "Last 7 days", "自我實驗": "Self-experiment", "目前沒有到期的複習。": "Nothing due right now.", "知識點": "Concept", "層級": "Level", "保留率": "Retention",
  "學習工坊": "Learning workshop", "適性診斷": "Adaptive placement test", "開始診斷": "Start", "知識點練習": "Practice a concept", "微課": "Micro-lesson", "示範題與空白練習": "Worked examples and faded practice",
  "排序題": "Parsons problems", "找 bug": "Find the bug", "預測輸出": "Predict the output", "解法比較": "Compare solutions", "英文題目術語表": "Glossary for English problems",
  "檢查": "Check", "答對了": "Correct", "再試一次": "Try again", "下一題": "Next", "搜尋": "Search", "寫筆記": "Write a note", "送出": "Submit", "設定目標": "Set a goal",
  "思路": "Thinking", "回想": "Recall", "反思": "Reflection", "自我解釋": "Self-explanation", "介面語言": "Interface language", "色盲友善配色": "Color-blind friendly colors",
  "用你自己的話解釋這題的解法": "Explain the solution in your own words", "完成日期預測": "Forecast", "每週需要": "Needed per week",
};

export const lang = () => pref.get("lang", "zh");
export const t = (zh) => (lang() === "en" && EN[zh]) || zh;

export function applyA11y() {
  document.documentElement.lang = lang() === "en" ? "en" : "zh-Hant";
  document.documentElement.dataset.cb = pref.get("colorblind", false) ? "1" : "0";
}
