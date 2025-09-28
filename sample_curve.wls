(* Usage: wolframscript -file sample_curve.wls "sin(x)+1" 0 6.28 201 *)
args = $ScriptCommandLine;
If[Length[args] < 5, Print["[]"]; Exit[0]];
exprStr = args[[2]]; aStr = args[[3]]; bStr = args[[4]]; nStr = args[[5]];

toWL[s_] := StringReplace[s, {
  "exp"->"Exp","log"->"Log","sin"->"Sin","cos"->"Cos","tan"->"Tan",
  "asin"->"ArcSin","acos"->"ArcCos","atan"->"ArcTan","sqrt"->"Sqrt",
  "pi"->"Pi","tau"->"(2 Pi)","e"->"E"
}];

fSym = ToExpression[toWL[exprStr], StandardForm, Function[x, Evaluate[#]] &];
a = ToExpression[toWL[aStr]]; b = ToExpression[toWL[bStr]];
n = ToExpression[nStr];

If[!NumericQ[a] || !NumericQ[b] || !IntegerQ[n] || n < 2, Print["[]"]; Exit[0]];
If[a > b, {a, b} = {b, a}];

data = Table[{x, N@fSym[x]}, {x, a, b, (b - a)/(n - 1)}];
Print@ExportString[data, "JSON"];
