# Test Code Review

## Diff

```diff
diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,5 +1,8 @@
 def calculate_total(items):
+    if not items:
+        return 0
+        
     total = 0
     for item in items:
-        total += item.price
+        total += item.get('price', 0)
     return total
```