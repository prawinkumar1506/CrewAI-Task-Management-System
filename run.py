# run.py
from app.chatbot.cli_chatbot import TaskCLI
from app.models.sample_data import populate_sample_data, SampleUser

def main():
    # Populate sample data if empty
    if SampleUser.objects.count() == 0:
        print("Populating sample data...")
        populate_sample_data()

    # Initialize and start the CLI
    cli = TaskCLI()
    cli.start()

if __name__ == "__main__":
    main()
