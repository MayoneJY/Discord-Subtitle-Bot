pipeline {
    agent any

    environment {
        DISCORD_BOT_TOKEN = credentials('DISCORD_BOT_TOKEN')
        DISCORD_BOT_AUTHOR_ID = credentials('DISCORD_BOT_AUTHOR_ID')
        DISCORD_BOT_NOTICE_CHANNEL_ID = credentials('DISCORD_BOT_NOTICE_CHANNEL_ID')
    }

    stages {
        stage('Clone') {
            steps {
                git branch: 'test', url: 'https://github.com/MayoneJY/Discord-Subtitle-Bot.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                export DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
                export DISCORD_BOT_AUTHOR_ID=${DISCORD_BOT_AUTHOR_ID}
                export DISCORD_BOT_NOTICE_CHANNEL_ID=${DISCORD_BOT_NOTICE_CHANNEL_ID}
                nohup python3 mayone.py > bot.log 2>&1 &
                '''
            }
        }
    }
}
