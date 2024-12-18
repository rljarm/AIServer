# project_root/orchestrator/orchestrator.py

import os
import subprocess
import asyncio
import logging
import json
from typing import List
from model_integration.my_model_wrapper import MyHostedModel
from langchain.utilities import GoogleSearchAPIWrapper
from model_integration.rag_chain import rag_search_and_store, add_resources_to_store
from twilio.rest import Client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AppBuilderOrchestrator:
    def __init__(self):
        self.project_name = ""
        self.requirements = {}
        self.search_results = {}
        self.max_iterations = 5
        self.model = MyHostedModel()
        self.search = GoogleSearchAPIWrapper(
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            google_cse_id=os.getenv("GOOGLE_CSE_ID")
        )
        self.twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        self.twilio_from = os.getenv("TWILIO_FROM_NUMBER")
        self.twilio_to = os.getenv("TWILIO_TO_NUMBER")

    async def send_sms(self, message: str):
        if self.twilio_client and self.twilio_from and self.twilio_to:
            self.twilio_client.messages.create(body=message, from_=self.twilio_from, to=self.twilio_to)

    async def gather_requirements(self, user_query: str):
        await self.send_sms("Gathering requirements...")
        self.requirements = await self.model.generate_requirements(user_query)
        self.project_name = self.requirements.get("app_name", "NewApp")
        logging.info(f"Requirements gathered: {json.dumps(self.requirements, indent=2)}")
        await self.send_sms(f"Requirements gathered for {self.project_name}")
        return self.requirements

    def generate_search_queries(self):
        features = self.requirements.get("features", [])
        queries = []
        for feature in features:
            frontend = self.requirements.get('frontend', {}).get('framework', 'React')
            queries.append(f"Best practices for implementing {feature} in {frontend}")
        return queries

    async def perform_search(self, queries: List[str]):
        await self.send_sms("Performing external searches...")
        for query in queries:
            results = await asyncio.get_event_loop().run_in_executor(None, self.search.run, query)
            top_docs = [r['snippet'] for r in results[:3]]
            # Add to RAG vector store
            await add_resources_to_store(top_docs)
            self.search_results[query] = top_docs
            logging.info(f"Search results for '{query}': {top_docs}")
        await self.send_sms("Search completed and indexed.")

    async def create_project_structure(self):
        await self.send_sms("Creating project structure...")
        directories = [
            f"{self.project_name}/frontend",
            f"{self.project_name}/backend",
            f"{self.project_name}/ios",
            f"{self.project_name}/tests",
            f"{self.project_name}/docs",
            f"{self.project_name}/configs"
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logging.info(f"Created directory: {directory}")
        await self.send_sms("Project structure created.")

    async def generate_code(self):
        await self.send_sms("Generating code...")
        await self.generate_frontend_code()
        await self.generate_backend_code()
        await self.generate_ios_code()
        await self.send_sms("Code generation complete.")

    async def generate_frontend_code(self):
        react_code = await self.model.generate_code("React", self.requirements)
        with open(f"{self.project_name}/frontend/App.js", "w") as f:
            f.write(react_code)
        logging.info("Generated React frontend code.")

    async def generate_backend_code(self):
        backend_code = await self.model.generate_code("Python", self.requirements)
        with open(f"{self.project_name}/backend/app.py", "w") as f:
            f.write(backend_code)
        logging.info("Generated Python backend code.")

    async def generate_ios_code(self):
        ios_code = await self.model.generate_code("SwiftUI", self.requirements)
        with open(f"{self.project_name}/ios/App.swift", "w") as f:
            f.write(ios_code)
        logging.info("Generated SwiftUI iOS app code.")

    async def lint_and_validate(self):
        await self.send_sms("Running linters...")
        lint_commands = [
            ["black", f"{self.project_name}/backend"],
            ["pylint", f"{self.project_name}/backend/app.py"],
            ["eslint", f"{self.project_name}/frontend"],
            ["swiftlint", f"{self.project_name}/ios"]
        ]

        for cmd in lint_commands:
            try:
                result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                logging.info(f"Linting successful: {' '.join(cmd)}")
            except subprocess.CalledProcessError as e:
                logging.error(f"Linting failed: {' '.join(cmd)}\nError: {e.stderr.decode()}")
                raise e
        await self.send_sms("Linting completed.")

    async def run_tests(self):
        await self.send_sms("Running tests...")
        backend_result = await self.run_subprocess(["pytest", f"{self.project_name}/backend/tests"], cwd=f"{self.project_name}/backend")
        frontend_result = await self.run_subprocess(["npm", "test"], cwd=f"{self.project_name}/frontend")
        ios_result = await self.run_subprocess(["xcodebuild", "test"], cwd=f"{self.project_name}/ios")
        all_passed = backend_result and frontend_result and ios_result
        if all_passed:
            logging.info("All tests passed successfully!")
            await self.send_sms("All tests passed successfully!")
        else:
            logging.warning("Some tests failed.")
            await self.send_sms("Some tests failed.")
        return all_passed

    async def run_subprocess(self, cmd, cwd=None):
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            logging.info(f"Command {' '.join(cmd)} executed successfully.")
            return True
        else:
            logging.error(f"Command {' '.join(cmd)} failed:\n{stderr.decode()}")
            return False

    async def fix_errors(self):
        await self.send_sms("Attempting to fix errors...")
        fixed = await self.model.fix_code(self.project_name)
        if fixed:
            logging.info("Errors fixed successfully.")
            await self.send_sms("Errors fixed, re-testing...")
        else:
            logging.warning("No fixes were applied.")
            await self.send_sms("No fixes applied.")

    async def iterate_until_success(self):
        for attempt in range(1, self.max_iterations + 1):
            logging.info(f"Test Attempt {attempt}")
            if await self.run_tests():
                return True
            else:
                logging.info("Fixing issues and retrying...")
                await self.fix_errors()
        logging.error("Maximum attempts reached. Tests still failing.")
        await self.send_sms("Max attempts reached, tests failing.")
        return False

    async def deploy(self):
        await self.send_sms("Deploying application...")
        try:
            await self.deploy_backend()
            await self.deploy_frontend()
            await self.deploy_ios()
            logging.info("All components deployed successfully.")
            await self.send_sms("Deployment successful.")
        except Exception as e:
            logging.error(f"Deployment failed: {e}")
            await self.send_sms("Deployment failed.")
            raise e

    async def deploy_backend(self):
        subprocess.run(["docker-compose", "build"], cwd=self.project_name, check=True)
        subprocess.run(["docker-compose", "push"], cwd=self.project_name, check=True)
        subprocess.run(["terraform", "apply", "-auto-approve"], cwd=f"{self.project_name}/configs/terraform", check=True)
        logging.info("Backend deployed.")

    async def deploy_frontend(self):
        subprocess.run(["vercel", "--prod"], cwd=f"{self.project_name}/frontend", check=True)
        logging.info("Frontend deployed.")

    async def deploy_ios(self):
        subprocess.run(["fastlane", "release"], cwd=f"{self.project_name}/ios", check=True)
        logging.info("iOS app deployed.")

    async def build_app(self, user_query: str):
        await self.gather_requirements(user_query)
        search_queries = self.generate_search_queries()
        if search_queries:
            await self.perform_search(search_queries)
        await self.create_project_structure()
        await self.generate_code()
        await self.lint_and_validate()
        success = await self.iterate_until_success()
        if success:
            await self.deploy()
        else:
            logging.warning("Skipping deployment due to test failures.")