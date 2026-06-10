pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "soc-app"
        CONTAINER_NAME = "soc-container"
    }

    stages {
        stage('Clone Repository') {
            steps {
                checkout scm
            }
        }

        stage('Dependency Audit (SCA)') {
            steps {
                script {
                    echo 'Running pip-audit for third-party vulnerabilities...'
                    sh 'pip install pip-audit'
                    sh 'pip-audit -r app/requirements.txt'
                }
            }
        }

        stage('Static Analysis (SAST)') {
            steps {
                script {
                    echo 'Running Bandit security analysis...'
                    sh 'pip install bandit'
                    sh 'bandit -r app/ -ll'
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    echo 'Building secure non-root Docker image...'
                    sh "docker build -t ${DOCKER_IMAGE} ."
                }
            }
        }

        stage('Stop Old Container') {
            steps {
                script {
                    echo 'Removing old running application instances...'
                    sh "docker rm -f ${CONTAINER_NAME} || true"
                }
            }
        }

        stage('Deploy New Container') {
            steps {
                script {
                    echo 'Running container with logs volume mount...'
                    sh "docker run -d -p 5000:5000 -v \$(pwd)/logs:/app/logs --name ${CONTAINER_NAME} ${DOCKER_IMAGE}"
                }
            }
        }
    }
}