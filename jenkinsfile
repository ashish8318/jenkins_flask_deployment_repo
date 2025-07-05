def imageTag = ''  // shared across stages
def pipelineStatus = true // shared across stages
def awsRegion = ''
def ecrRepo = ''
def gitRepo = ''
def awsAccountId = ''
def assumeRoleArn = ''
def sessionName = 'jenkins-session'

pipeline {
    agent any

    stages {
        stage("Load Env from Credentials") {
            steps {
                withCredentials([
                    string(credentialsId: 'AWS_REGION', variable: 'AWS_REGION'),
                    string(credentialsId: 'ECR_REPO', variable: 'ECR_REPO'),
                    string(credentialsId: 'GIT_REPO', variable: 'GIT_REPO'),
                    string(credentialsId: 'AWS_ACCOUNT_ID', variable: 'AWS_ACCOUNT_ID'),
                    string(credentialsId: 'ASSUME_ROLE_ARN', variable: 'ASSUME_ROLE_ARN')
                ]) {
                    script {
                        awsRegion = AWS_REGION
                        ecrRepo = ECR_REPO
                        gitRepo = GIT_REPO
                        awsAccountId = AWS_ACCOUNT_ID
                        assumeRoleArn = ASSUME_ROLE_ARN
                    }
                }
            }
        }

        stage("Code Checkout") {
            steps {
                echo "📦 Cloning repository..."
                git url: gitRepo, branch: "main"
            }
            post {
                success {
                    echo "Code Successfully Cloned"
                }
            }
        }

        stage("Assume Role") {
            steps {
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: 'aws-creds-id'
                ]]) {
                    bat """
                    echo 🔄 Assuming role...
                    aws sts assume-role --role-arn "${assumeRoleArn}" --role-session-name "${sessionName}" --region "${awsRegion}" > assume_output.json
                    """
                }
                powershell '''
                Write-Output "🔐 Setting temporary credentials from assume_output.json"
                $json = Get-Content assume_output.json | ConvertFrom-Json
                [Environment]::SetEnvironmentVariable("AWS_ACCESS_KEY_ID", $json.Credentials.AccessKeyId, "Process")
                [Environment]::SetEnvironmentVariable("AWS_SECRET_ACCESS_KEY", $json.Credentials.SecretAccessKey, "Process")
                [Environment]::SetEnvironmentVariable("AWS_SESSION_TOKEN", $json.Credentials.SessionToken, "Process")
                Write-Output "✅ Temporary credentials set"
                '''
            }
        }

        stage('Export AWS Credentials to .bat') {
            steps {
                powershell '''
                $json = Get-Content assume_output.json | ConvertFrom-Json

                $lines = @(
                    "@echo off",
                    "set AWS_ACCESS_KEY_ID=$($json.Credentials.AccessKeyId)",
                    "set AWS_SECRET_ACCESS_KEY=$($json.Credentials.SecretAccessKey)",
                    "set AWS_SESSION_TOKEN=$($json.Credentials.SessionToken)"
                )

                $lines | Out-File -FilePath aws-creds.bat -Encoding ASCII -Force
                '''
            }
        }

        stage('Get Latest ECR Image Tag') {
            steps {
                script {
                    // Preprocess ECR repo name to extract only the repo name
                    def repoName = ecrRepo.split("/")[-1]  // "jenkins-pipeline"

                    imageTag = bat(
                        script: """
                        call aws-creds.bat
                        for /f "usebackq delims=" %%i in (`aws ecr describe-images ^
                            --repository-name ${repoName} ^
                            --region ${awsRegion} ^
                            --query "sort_by(imageDetails,& imagePushedAt)[-1].imageTags[0]" ^
                            --output text`) do @echo %%i
                        """,
                        returnStdout: true
                    ).trim()

                    echo "🔖 Latest image tag: ${imageTag}"
                }
            }
        }


        stage('Generate Version Tag') {
            steps {
                script {
                    imageTag = imageTag?.isInteger() ? (imageTag.toInteger() + 1).toString() : '1'
                    echo "🔖 New version tag: ${imageTag}"
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                bat """
                call aws-creds.bat
                echo 🛠️ Building Docker image...
                docker build -t ${ecrRepo}:${imageTag} .
                """
            }
        }

        stage('Login to ECR') {
            steps {
                bat """
                call aws-creds.bat
                echo 🔐 Logging into ECR...
                aws ecr get-login-password --region ${awsRegion} | docker login --username AWS --password-stdin ${ecrRepo.split("/")[0]}
                """
            }
        }


        stage('Push Image') {
            steps {
                bat """
                call aws-creds.bat
                echo 🚀 Pushing Docker image...
                docker push ${ecrRepo}:${imageTag}
                """
            }
        }
    }

    post {
        success {
            echo '✅ Pipeline completed successfully.'
        }
        failure {
            echo '❌ Pipeline failed.'
        }
    }
}
