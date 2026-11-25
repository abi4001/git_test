import torch
a=torch.tensor([3,5])
b=torch.zeros(2,3,5)
c=torch.ones(9,8)
d=torch.rand(11,4)

a1 = torch.tensor([10, 20, 30])
b1 = torch.tensor([1, 2, 3])

#arthimetic operation
print(a1 + b1)
print(a1 - b1)
print(a1 * b1)
print(a1 / b1)

#matric multiplication
c1=torch.tensor([[2,3,4],[5,6,7],[3,5,8]])
c2=torch.tensor([[0,9,8],[6,9,7],[8,3,5]])
result=torch.matmul(c1,c2)
print(result)

print("\n values:",a.shape)
print(a.device)
print(a.dtype)
print("\t",a, "\n",b,"\\n",c)
print(d)

    

