(* ::Package:: *)

(* Usage:
   wolframscript -file compute_volume.wls "exp(x)+sin(x)" 0 5
   -> prints JSON with fields: functionWL, functionTeX, integralTeX, volumeExact, volumeNumeric, yMaxNumeric
*)

args = $ScriptCommandLine;
If[Length[args] < 4,
  Print["{}"]; Exit[0];
];

exprStr = args[[2]];
aStr    = args[[3]];
bStr    = args[[4]];

(* Map common Python/NumPy-style names to Wolfram Language *)
toWL[s_] := StringReplace[s, {
    "exp" -> "Exp", "log" -> "Log",
    "sin" -> "Sin", "cos" -> "Cos", "tan" -> "Tan",
    "asin" -> "ArcSin", "acos" -> "ArcCos", "atan" -> "ArcTan",
    "sqrt" -> "Sqrt",
    "pi" -> "Pi", "tau" -> "(2 Pi)", "e" -> "E"
}];

exprWLstr = toWL[exprStr];

(* Parse numeric limits: allow 'pi', '2*pi', etc. *)
safeToExpr[s_] := ToExpression[toWL[s], StandardForm, Hold];
aHold = safeToExpr[aStr]; bHold = safeToExpr[bStr];
a = ReleaseHold[aHold]; b = ReleaseHold[bHold];
If[! NumericQ[a] || ! NumericQ[b], Print["{}"]; Exit[0]];

If[a > b, {a, b} = {b, a}];

(* Build f[x] from string safely *)
fSym = ToExpression[exprWLstr, StandardForm, Function[x, Evaluate]()]()
