"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.calculateFocusTarget = calculateFocusTarget;
const UI_js_1 = require("../UI.js");
function calculateFocusTarget(days, getModifiers, isSelected, lastFocused) {
    let focusTarget;
    let index = 0;
    let found = false;
    while (index < days.length && !found) {
        const day = days[index];
        const modifiers = getModifiers(day);
        if (!modifiers[UI_js_1.DayFlag.disabled] &&
            !modifiers[UI_js_1.DayFlag.hidden] &&
            !modifiers[UI_js_1.DayFlag.outside]) {
            if (modifiers[UI_js_1.DayFlag.focused]) {
                focusTarget = day;
                found = true;
            }
            else if (lastFocused?.isEqualTo(day)) {
                focusTarget = day;
                found = true;
            }
            else if (isSelected(day.date)) {
                focusTarget = day;
                found = true;
            }
            else if (modifiers[UI_js_1.DayFlag.today]) {
                focusTarget = day;
                found = true;
            }
        }
        index++;
    }
    if (!focusTarget) {
        // return the first day that is focusable
        focusTarget = days.find((day) => {
            const m = getModifiers(day);
            return !m[UI_js_1.DayFlag.disabled] && !m[UI_js_1.DayFlag.hidden] && !m[UI_js_1.DayFlag.outside];
        });
    }
    return focusTarget;
}
//# sourceMappingURL=calculateFocusTarget.js.map