from unittest import result
import ftfy
result = ftfy.fix_text('é▄é╡éδé¡éδ.txt')
print(result)  # 输出: '✓ No problems'
