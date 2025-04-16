![Lint-free](https://github.com/nyu-software-engineering/containerized-app-exercise/actions/workflows/lint.yml/badge.svg)
![ML Client Build & Test](https://github.com/software-students-spring2025/4-containers-buythedip/actions/workflows/ml_client.yml/badge.svg)
![Web App Build & Test](https://github.com/software-students-spring2025/4-containers-buythedip/actions/workflows/web_app.yml/badge.svg)

# Containerized Fruit Recognition App
Project 4 of Software Engineering (CSCI-UA 474) course.
This project is a fully containerized system composed of three components:

- A **Flask web app** to upload images and display classification results
- A **machine learning client** that performs fruit image classification
- A **MongoDB** database to store uploaded images and classification metadata

The system uses a webcam to capture fruit images, identifies the fruit via a machine learning model, and fetches a descriptive definition using the Merriam-Webster API. It is designed to be extended with features such as **audio feedback**, making it useful for visually impaired users or interactive learning environments.

---

## Prerequisites

Before running this app, make sure the following are installed:
- [Docker Desktop](https://www.docker.com/products/docker-desktop)

### Windows with WSL 2
If you are using **Windows with WSL 2**, you have two options:

#### Option 1: Enable Docker Desktop WSL 2 Integration (Recommended)
1. Open Docker Desktop
2. Go to **Settings → Resources → WSL Integration**
3. Enable integration for your Linux distro (e.g., Ubuntu)
4. Click **Apply & Restart**

To verify that Docker is available in WSL, run:
```bash
docker --version
docker compose version
```

After installation, verify with:
```bash
docker --version
docker compose version
```

### Mac
For macOS users, ensure that Docker Desktop is running before proceeding. You can verify Docker is working with:
```bash
docker --version
docker compose version
```

## Running the App

### 1. Clone the Repository

```bash
git clone git@github.com:cl3880/containerized-app-project.git
cd containerized-app-project
```

### 2. Set Up Environment Variables
Copy the example `.env` file and add your Merriam-Webster API key:

```bash
cp env.example .env
```

Edit `.env` with the following content:
```
MW_API_KEY=your_mw_api_key_here
MW_URL=https://dictionaryapi.com/api/v3/references/collegiate/json
MONGODB_URI=mongodb://mongodb:27017/containerapp
ML_CLIENT_URI=http://ml_client:5000
```

> **Important**: You need a valid Merriam-Webster API key for the definition feature to work. You can get a free API key at the [Merriam-Webster Developer Center](https://dictionaryapi.com/).

### 3. Build and Start All Containers

```bash
docker compose up --build
```
This command will:
- Build the Flask web app container
- Build the ML client container
- Start the MongoDB container
- Link all three containers together

> This project uses `docker compose`. If you're using legacy Docker, use `docker-compose` instead.

### 4. Access the Application
After the build completes, open your browser to:
```
http://localhost:5001
```

### 5. Stopping the Application
To stop the application, press `Ctrl+C` in the terminal where Docker Compose is running, or run:
```bash
docker compose down
```

## Manual Testing
For manual integration testing, you can simulate image uploads using a test script.
Two classification images are included in `web-app/tests/test_data/` and two sample training images in `web-app/tests/sample_training_images`

You can use the `test_upload.py` ssript to sen test images to the app without using the UI:
```bash
python -m web-app.tests.test_upload banana
```

Replace `banana` with one of:
- `apple`
- `banana`
- `train_apple`
- `train_banana`

## Team Members
[Mahmoud Shehata](https://github.com/MahmoudS1201) <br /> 
[Patrick Cao](https://github.com/Novrain7) <br />
[Chris Leu](https://github.com/cl3880) <br />
[Syed Naqvi](https://github.com/syed1naqvi)

## License
This project is licensed under the GNU General Public License. See the [LICENSE](https://github.com/software-students-spring2025/4-containers-buythedip/blob/main/LICENSE) file for details.