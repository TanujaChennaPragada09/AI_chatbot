-- chat_db.sql

-- 1. Create database
CREATE DATABASE IF NOT EXISTS chatbot_db;

-- 2. Create user
CREATE USER IF NOT EXISTS 'Chat_user'@'%' IDENTIFIED BY 'Admin@123';

-- 3. Grant privileges
GRANT ALL PRIVILEGES ON chatbot_db.* TO 'Chat_user'@'%';

-- 4. Apply privileges
FLUSH PRIVILEGES;
