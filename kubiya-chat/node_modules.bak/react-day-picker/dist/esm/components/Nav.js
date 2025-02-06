import React from "react";
import { UI } from "../UI.js";
import { useDayPicker } from "../useDayPicker.js";
/**
 * Render the toolbar with the navigation button.
 *
 * @group Components
 * @see https://daypicker.dev/guides/custom-components
 */
export function Nav(props) {
    const { onPreviousClick, onNextClick, previousMonth, nextMonth, ...navProps } = props;
    const { components, classNames, labels: { labelPrevious, labelNext } } = useDayPicker();
    return (React.createElement("nav", { ...navProps },
        React.createElement(components.PreviousMonthButton, { type: "button", className: classNames[UI.PreviousMonthButton], tabIndex: previousMonth ? undefined : -1, disabled: previousMonth ? undefined : true, "aria-label": labelPrevious(previousMonth), onClick: props.onPreviousClick },
            React.createElement(components.Chevron, { disabled: previousMonth ? undefined : true, className: classNames[UI.Chevron], orientation: "left" })),
        React.createElement(components.NextMonthButton, { type: "button", className: classNames[UI.NextMonthButton], tabIndex: nextMonth ? undefined : -1, disabled: nextMonth ? undefined : true, "aria-label": labelNext(nextMonth), onClick: props.onNextClick },
            React.createElement(components.Chevron, { disabled: nextMonth ? undefined : true, orientation: "right", className: classNames[UI.Chevron] }))));
}
//# sourceMappingURL=Nav.js.map