#!/bin/bash

export AWS_ACCESS_KEY_ID=AKIA2FA7DQGYCLEJYFPX
export AWS_SECRET_ACCESS_KEY=aeSjgWRTSCDwiMNIVZ3JeVMJqE38HNKFpxe
export AWS_STORAGE_BUCKET_NAME=ctrl-ai-hack-hello-world-s3
export AWS_S3_REGION_NAME=ap-south-1

# Apply database migrations
echo "🛠Running makemigrations and migrate..."
python manage.py makemigrations
python manage.py migrate

# Start Django dev server
echo "🚀 Starting Django server..."
python manage.py runserver 0.0.0.0:8000 &

# Start frontend (Vite/CRA dev server)
echo "🌐 Starting Node dev server..."
cd UI
npm run dev -- --host 0.0.0.0
