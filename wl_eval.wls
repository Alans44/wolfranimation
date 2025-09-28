(* wl_eval.wls — parse an expression string -> samples + TeX as JSON *)
SetOptions[$Output, PageWidth -> Infinity];

args = $ScriptCommandLine;
If[Length[args] < 2,
  Print @ ExportString[<|"ok"->False,"error"->"Usage: wolframscript -file wl_eval.wls <expr> [xmin] [xmax]"|>, "RawJSON"];
  Exit[1];
];

exprStr = args[[2]];
xmin = If[Length[args] >= 3, Quiet@Check[ToExpression[args[[3]]], -2.0], -2.0];
xmax = If[Length[args] >= 4, Quiet@Check[ToExpression[args[[4]]],  2.0],  2.0];
If[xmin >= xmax, Print @ ExportString[<|"ok"->False,"error"->"xmin must be < xmax"|>, "RawJSON"]; Exit[1]];

expr = Quiet @ Check[ ToExpression[exprStr], $Failed ];
If[expr === $Failed || !FreeQ[expr, y] || Head[expr] === Symbol,
  Print @ ExportString[<|"ok"->False,"error"->"Could not parse expression", "expr"->exprStr|>, "RawJSON"]; Exit[1];
];

xs = Subdivide[xmin, xmax, 239];
ys = Quiet @ Check[(expr /. x -> #) & /@ xs, $Failed];
If[ys === $Failed || !VectorQ[ys, NumericQ],
  Print @ ExportString[<|"ok"->False,"error"->"Expression not numeric on domain","expr"->exprStr|>, "RawJSON"]; Exit[1];
];

samples = Transpose @ {N@xs, N@ys};
tex = ToString @ TeXForm[expr];

Print @ ExportString[
  <|"ok"->True, "mode"->"equation", "tex"->("y="<>tex), "domain"->{xmin,xmax}, "samples"->samples|>,
  "RawJSON"
];
