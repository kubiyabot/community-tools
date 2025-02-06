"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.Nav = Nav;
const react_1 = __importDefault(require("react"));
const UI_js_1 = require("../UI.js");
const useDayPicker_js_1 = require("../useDayPicker.js");
/**
 * Render the toolbar with the navigation button.
 *
 * @group Components
 * @see https://daypicker.dev/guides/custom-components
 */
function Nav(props) {
    const { onPreviousClick, onNextClick, previousMonth, nextMonth, ...navProps } = props;
    const { components, classNames, labels: { labelPrevious, labelNext } } = (0, useDayPicker_js_1.useDayPicker)();
    return (react_1.default.createElement("nav", { ...navProps },
        react_1.default.createElement(components.PreviousMonthButton, { type: "button", className: classNames[UI_js_1.UI.PreviousMonthButton], tabIndex: previousMonth ? undefined : -1, disabled: previousMonth ? undefined : true, "aria-label": labelPrevious(previousMonth), onClick: props.onPreviousClick },
            react_1.default.createElement(components.Chevron, { disabled: previousMonth ? undefined : true, className: classNames[UI_js_1.UI.Chevron], orientation: "left" })),
        react_1.default.createElement(components.NextMonthButton, { type: "button", className: classNames[UI_js_1.UI.NextMonthButton], tabIndex: nextMonth ? undefined : -1, disabled: nextMonth ? undefined : true, "aria-label": labelNext(nextMonth), onClick: props.onNextClick },
            react_1.default.createElement(components.Chevron, { disabled: nextMonth ? undefined : true, orientation: "right", className: classNames[UI_js_1.UI.Chevron] }))));
}
//# sourceMappingURL=Nav.js.map