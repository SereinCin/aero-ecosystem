import sys
sys.path.insert(0, "src")
import kernel
print(repr(kernel.search("a", "{not json}")))
print(repr(kernel.search("a", '{"a": }')))
print(repr(kernel.search("a", "")))
print(repr(kernel.search("a", "[")))
