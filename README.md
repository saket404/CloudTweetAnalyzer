# CloudTweetAnalyzer

COMP90024 Assignment 2 -  Develop a Cloud-based solution that exploits a multitude of virtual machines (VMs) across the UniMelb Research Cloud for harvesting tweets through the Twitter APIs (using both the Streaming and the Search API interfaces). Develop a social analytics dashboard utilising data from Aurin and twitter. 

![Social Analytics Dashboard](/Dashboard.png "Social Analytics Dashboard")

## Standard Full Deployment

1. Download the openrc.sh file from the Unimelb Research Cloud, and save it in the root of the Ansible project folder, replacing the existing "openrc.sh" file.
    
2. Make sure you have a key-pair configured on your Unimelb Research Cloud and local machine, and change the "instance\_key\_name" variable to match your key-pair name in the "nectar.yaml" and "nectar-scale-up.yaml" files.
    
3. Generate and save your Openstack API password, for the Research Cloud, somewhere on your local machine, and have it ready when running the script as you will be prompted for it.
    
4. Make sure the desired resources are correctly set in the "nectar.yaml" host variable file. The current default resources is 4 compute instances, 8 volumes, 4 volume snapshots with 240GB total.
    
5. Run the "run-jam.sh" shell script inside the root of the "twitter\_jam" folder.
    
6. The user will be prompted for their OpenStack password, and then their local machine password. When the script first connects to the instances, the user will be prompted to confirm the host fingerprints, which is the last prompt. Once the script is done, the Twitter harvester will be automatically running and populating the database.


## Scale Up Deployment
The scale up deployment script is written with the assumption that the standard full deployment script was previous run, and the user wishes to increase the number of deployed instances, Couch-DB nodes, and Twitter harvesters.

1. Download the openrc.sh file from the Unimelb Research Cloud, and save it in the root of the Ansible project folder, replacing the existing openrc.sh file.
    
2. Make sure you have a key-pair configured on your Unimelb Research Cloud and local machine, and change the "instance\_key\_name" variable to match your key-pair name in the "nectar.yaml" and "nectar-scale-up.yaml" files.
    
3. The user will need to setup the IP for the master node in the Couch-DB cluster, by setting the "master\_node\_ip" to the IP of the jam-1 node in the "jam-scale-up.yaml" file.
    
4. Generate and save your Openstack API password, for the Research Cloud, somewhere on your local machine, and have it ready when running the script as you will be prompted for it.
    
5. Make sure the desired resources to be added are correctly set in the "nectar-scale-up.yaml" host variable file. The current default resources is 1 compute instances, 2 volumes, 1 volume snapshots with 35GB total.
    
6. Run the "run-jam-scale-up.sh" shell script inside the root of the "twitter\_jam" folder.
    
7. The user will be prompted for their OpenStack password, and then their local machine password. When the script first connects to the instances, the user will be prompted to confirm the host fingerprints, which is the last prompt. Once the script is done, the Twitter harvester will be automatically running and populating the database.


## User Interface guide
This is a guide for user of how to use our front-end. User can perform several actions to visualize our scenario.

1. In Scenario Tab, user can switch the tab to view the scenario desired by clicking on the tab.
    
2. In scenario 1, the user can select which AURIN data to correlate by using drop down option and select it. It will automatically load the plot.
    
3. In each of the plot object, the user can select the specific region of the plot by draw a rectangle on the graph which it will automatically zoom. User can gloss over the point in the plot and user can observe the data information such as tweet, sentiment analytic and etc. 
    
4. In each of the plot object, the user can select the city not to show on the plot by clicking on the city name on the right hand of the plot. The plot will remove the selected city and show the remaining ones.
    
5. The user can export the plot as an image by using the mouse the gloss over the plot and click on the image icon which it automatically generates an image and download for the user.
    
6. The user can zoom in and out by using scrolling gesture and user can gloss over to the point to see the tweet.

