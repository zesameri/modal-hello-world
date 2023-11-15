import modal

app_name = "hello-world"
f = modal.Function.lookup(app_name, "f")
cid = f.remote(1000)
total = 0
for ret in f.map(range(20)):
    total += ret
