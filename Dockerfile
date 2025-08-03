# استخدام Python 3.11 كصورة أساسية
FROM python:3.11-slim

# تعيين متغير البيئة لمنع إنشاء ملفات .pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# تعيين مجلد العمل
WORKDIR /app

# تثبيت المتطلبات النظام
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملف المتطلبات وتثبيت المكتبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ ملفات التطبيق
COPY . .

# إنشاء مجلد الرفع
RUN mkdir -p uploads

# تعيين المنفذ
EXPOSE 5000

# تشغيل التطبيق باستخدام gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "120", "app:app"]

