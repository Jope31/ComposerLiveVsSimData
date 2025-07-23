# **Composer Multi-Symphony Data Fetcher**

This project provides a Python script system to automatically download live and backtest performance data for multiple Composer symphonies at once. The output is a clean, consolidated CSV format, perfect for pasting into Google Sheets or Excel for performance analysis and charting.

This system uses a secure, automated login process. After a one-time setup, you will not need to enter your credentials again.

This guide is designed for users on **Windows 11** with little to no prior coding experience.

## **Part 1: Initial Setup (One-Time Only)**

First, you need to set up your computer with the necessary tools.

#### **1\. Install Python from the Microsoft Store**

* Open the **Microsoft Store** app on Windows 11\.  
* Search for "Python" and install the most recent version (e.g., Python 3.11 or newer). This is the easiest method as it automatically configures Python for your system.

#### **2\. Install Required Libraries**

* Open the Windows **Command Prompt** (search for cmd in the Start Menu).  
* In the command prompt window, type the following command and press **Enter**:

pip install requests python-dateutil

* This installs two helper libraries the scripts need to run.

## **Part 2: Creating the Scripts**

This system uses a "master" script to run one or more "group" scripts, all managed by a central authentication script. You must save all of these files in the **same folder** (e.g., a new folder in Documents called ComposerScripts).

#### **1\. Create the** auth.py **Script**

This file handles the secure login process.

* Copy the code from auth.py into your scripts folder.

#### **2\. Create the Master Runner Scripts**

These are the main scripts you will execute.

* Copy the code for both master\_runner.py and monthly\_master\_runner.py into your scripts folder.  
* Create symphony group sets based on start date. Do this by copying a file like 530symphs.py into your scripts folder and adjust the symphonies there based on yours for that start date. Then change the start date listed below them.  
  * If you have multiple symphonies, then copy over multiple files  
* Adjust the SYMPHONY\_SCRIPT\_FILES names in the master\_runner.py to the file names containing your symphony groups based on start date.

#### **3\. Create Your Symphony Group Scripts**

You will create a separate file for each group of symphonies you want to run.

* For running monthly data, copy the  all\_symphs\_monthly.py to your folder and adjust the symphonies to your set.  
* **Repeat this process for each group of symphonies**, saving each as a new file in the same folder.

## **Part 3: Finding Your Composer Credentials**

For the one-time setup, you will need three pieces of information: your Composer **API Key**, your **Secret Key**, and your **Account ID**.

#### **1\. Generate Your API Key and Secret Key**

* Log in to your Composer account.  
* Navigate to **Settings \> API Keys**.  
* Click **"Create Key"** to generate a new API Key and Secret Key pair.  
* **Important:** Copy the **Secret Key** immediately and save it somewhere secure, as it will only be shown once.

#### **2\. Find Your Account ID**

* While logged in to app.composer.trade, press **F12** to open Developer Tools.  
* Click the **"Network"** tab and select the **"Fetch/XHR"** filter.  
* Reload the page (**F5**).  
* In the "Filter" box, type symphonies.  
* Click on one of the requests in the list.  
* Under the **"Headers"** tab, find the **Request URL**. Your Account ID is the long string between /accounts/ and /symphonies/.

## **Part 4: Configuring Your Scripts**

#### **1\. Configure the Master Scripts**

* Open master\_runner.py and monthly\_master\_runner.py with a text editor.  
* In the SYMPHONY\_SCRIPT\_FILES or MONTHLY\_SCRIPT\_FILES list, make sure the filenames exactly match the symphony group files you created.

#### **2\. Configure Each Symphony Group Script**

* Open one of your symphony group files (e.g., 530symphs.py).  
* Update the configuration section at the top:  
  * SYMPHONIES: Add the names and IDs of all the symphonies that belong in this group.  
  * START\_DATE: Set the correct start date for this group (this is only in the main template, not the monthly one).  
* Save the file and repeat for each of your symphony group scripts.

## **Part 5: Running the System**

#### **1\. Run a Master Script**

* Open a new **Command Prompt** and navigate to your scripts folder (e.g., cd Documents\\ComposerScripts).  
* Run one of the master scripts:

python master\_runner.py

or

python monthly\_master\_runner.py

#### **2\. First-Time Login**

* The very first time you run a master script, it will prompt you for your **API Key**, **Secret Key**, and **Account ID**.  
* Enter these details. The script will then save them securely in a composer\_credentials.json file so you don't have to enter them again.  
* NOTE: the file will store your API key and secret in plain text\! Consider using “cryptography” to encrypt it.  
* https://stackoverflow.com/questions/61607367/how-to-encrypt-json-in-python

#### **3\. Subsequent Runs**

* After the first time, the script will automatically use the saved credentials.  
* If you run monthly\_master\_runner.py, it will still ask you for the **Start Date** for your analysis.

#### **4\. Use the Output**

* Once the script is finished, copy the CSV-formatted data from the command prompt.  
* Open a **Google Sheet**, click on cell A1, and paste the data.

## **Troubleshooting**

#### **"Authentication failed. Cannot proceed."**

If you see this error, it means your saved credentials have become invalid (this can happen if you revoke your API key).

**Solution:**

1. Find the file named composer\_credentials.json in your scripts folder.  
2. **Delete** this file.  
3. Run the master script again. It will prompt you to enter your API Key, Secret, and Account ID, which will create a new, valid credentials file.

