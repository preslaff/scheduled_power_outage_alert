# Scheduled Power Outage Alert for the customers of ERP SEVER in Bulgaria
This is an automation script which alerts the customers of ERP SEVER by whatsapp for scheduled power outages

##Abstsract
Giving the short-sightedness of the ERP SEVER management, there is no any practical way to be warned when the company performs their scheduled repairs of the power grid that they support. This leads to numerous difficulties for ordinary and business users, because they do not know in advance when and for how long they will be without electricity. They publish the information 48 hours before the outage on their web site in  a very inappropriate and difficult to automate data format. This simple s solution provides a way for electricity consumers to subscribe to notifications about upcoming power outages by specifying their area, town and phone number.

##How to install
1. First you need to install the needed python libraries: `pip install selenuim pywhatkit schedule webdriver_manager`
2. Start the erpsever_alert_pywhatkit.py
3. Input the information when asked from the script

##How the script sends the alerts
The script uses `pywhatkit` and that's why you have to open your Whatsapp account in your browser. This is a development version and this is the simplest way to use Whatsapp notifications. If you want to integrate the solution in production environment you can use the Twilio service (just use the erpsever_twilio.py script)
