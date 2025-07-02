pipeline {
  agent any

  environment {
    IMAGE_TAG = '' // will be set later dynamically
    ROLE_ARN = 'arn:aws:iam::<ACCOUNT_ID>:role/ECRPushRole' // Update with your actual role ARN
  }

  stages {
    stage('Load Env from Credentials') {
      steps {
        withCredentials([
          string(credentialsId: 'AWS_REGION', variable: 'AWS_REGION'),
          string(credentialsId: 'ECR_REPO', variable: 'ECR_REPO'),
          string(credentialsId: 'GIT_REPO', variable: 'GIT_REPO'),
          string(credentialsId: 'AWS_ACCOUNT_ID', variable: 'AWS_ACCOUNT_ID'),
          string(credentialsId: 'GIT_AUTHOR_EMAIL', variable: 'AUTHOR_EMAIL'),
          string(credentialsId: 'GIT_AUTHOR_NAME', variable: 'AUTHOR_NAME')
        ]) {
          script {
            env.AWS_REGION = AWS_REGION
            env.ECR_REPO = ECR_REPO
            env.GIT_REPO = GIT_REPO
            env.AWS_ACCOUNT_ID = AWS_ACCOUNT_ID
            env.AUTHOR_EMAIL = AUTHOR_EMAIL
            env.AUTHOR_NAME = AUTHOR_NAME
          }
        }
      }
    }

    stage('Checkout Code') {
      steps {
        git url: "${env.GIT_REPO}", branch: 'main'
      }
    }

    stage('Assume Role and Build & Push Docker Image') {
      steps {
        script {
          def repoUri = "${env.ECR_REPO}"

          // Step 1: Assume Role
          bat """
          powershell -Command \"
          \$role = aws sts assume-role --role-arn '${ROLE_ARN}' --role-session-name 'jenkins-session' | ConvertFrom-Json;
          \$env:AWS_ACCESS_KEY_ID = \$role.Credentials.AccessKeyId;
          \$env:AWS_SECRET_ACCESS_KEY = \$role.Credentials.SecretAccessKey;
          \$env:AWS_SESSION_TOKEN = \$role.Credentials.SessionToken;

          # Step 2: Login to ECR
          aws ecr get-login-password --region ${env.AWS_REGION} |
            docker login --username AWS --password-stdin ${repoUri};

          # Step 3: Determine next image tag
          \$tags = aws ecr list-images --repository-name ${env.ECR_REPO} --region ${env.AWS_REGION} --query 'imageIds[*].imageTag' --output text;
          \$numTags = \$tags -split '\\s+' | Where-Object { \$_ -match '^[0-9]+$' } | ForEach-Object { [int]\$_ };
          \$nextTag = (\$numTags | Measure-Object -Maximum).Maximum + 1;
          if (!\$nextTag) { \$nextTag = 1 }
          echo IMAGE_TAG=\$nextTag > tag.txt
          \"
          """

          // Step 4: Load IMAGE_TAG
          def tag = readFile('tag.txt').trim().split('=')[1]
          env.IMAGE_TAG = tag
          echo "Using image tag: ${env.IMAGE_TAG}"

          // Step 5: Build and Push Docker Image
          bat """
          docker build -t ${repoUri}:${env.IMAGE_TAG} .
          docker push ${repoUri}:${env.IMAGE_TAG}
          """
        }
      }
    }
  }
}
