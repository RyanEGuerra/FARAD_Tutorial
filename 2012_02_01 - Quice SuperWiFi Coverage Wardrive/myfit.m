% Fminsearch code
function sse = myfit(params, Input, Actual_Output)
C = params(1);
A = params(2);
lamda = params(3);
Fitted_Curve=C + A.*exp(-lamda*Input);
Error_Vector=Fitted_Curve - Actual_Output;
% When curvefitting, a typical quantity to
% minimize is the sum of squares error
sse=sum(Error_Vector.^2);
% You could also write sse as
% sse=Error_Vector(:)'*Error_Vector(:);