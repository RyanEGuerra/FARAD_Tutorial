% Fminsearch code
function diff = calc_diff(params, Input, Actual_Output)
C = params(1);
A = params(2);
lamda = params(3);
diff = C + A.*exp(-lamda*Input) - Actual_Output;