// src/primitives/branchPicker/BranchPickerRoot.tsx
import { Primitive } from "@radix-ui/react-primitive";
import { forwardRef } from "react";
import { If } from "../message/index.mjs";
import { jsx } from "react/jsx-runtime";
var BranchPickerPrimitiveRoot = forwardRef(({ hideWhenSingleBranch, ...rest }, ref) => {
  return /* @__PURE__ */ jsx(If, { hasBranches: hideWhenSingleBranch ? true : void 0, children: /* @__PURE__ */ jsx(Primitive.div, { ...rest, ref }) });
});
BranchPickerPrimitiveRoot.displayName = "BranchPickerPrimitive.Root";
export {
  BranchPickerPrimitiveRoot
};
//# sourceMappingURL=BranchPickerRoot.mjs.map