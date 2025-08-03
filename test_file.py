#!/usr/bin/env python3
# ملف اختبار لتجربة رفع الملفات

print("مرحبا! هذا ملف تم رفعه وتشغيله بنجاح")
print("التاريخ والوقت الحالي:")

import datetime
now = datetime.datetime.now()
print(f"التاريخ: {now.strftime('%Y-%m-%d')}")
print(f"الوقت: {now.strftime('%H:%M:%S')}")

print("\nقائمة الأرقام من 1 إلى 10:")
for i in range(1, 11):
    print(f"الرقم: {i}")

print("\nتم تنفيذ الملف بنجاح!")

