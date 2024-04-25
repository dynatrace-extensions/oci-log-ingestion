# Ingest OCI logs into Dynatrace
With the OCI Log ingest function, OCI users can stream their logs directly into Dynatrace for troubleshooting and root cause analysis using Davis® AI.  
This OCI function was created to work alongside the Oracle Cloud Infrastructure extension found on the Dynatrace Hub.

### Getting Started
**Note:** These actions must be done by a OCI tenancy administrator using the Oracle Cloud Shell or editor.

**OCI logs**
1. Login to the OCI portal and search for *Log Groups*
1. Select your compartment on the left side and click Create Log Group - A side will open.
2. Enter your desired name, description and any tags.
3. Click Create to create your new Log Group.
4. One again, search for and select *Logs*.
5. Click to Create custom log or Enable service log. Enter a name and select your log group.
6. Click *Create custom log* to create your custom log.

**OCI function**
1. In the OCI portal, navigate to Functions.
2. Select an existing application or click *Create Application*.
3. Create a new OCI function within your application. 
4. We recommend using the Oracle Code Editor to create your custom function. 
5. Once the Code Editor is open, select *Create from code repository* and enter a function name and the url to this Github repository. 
6. Edit the `func.yaml` file, updating the `DYNATRACE_TENANT` and `DYNATRACE_API_KEY` environment variables with the url to your Dynatrace tenant and an api token with the `logs.ingest` scope.
7. Follow the instructions on the *Getting started* page under your application. Use the cloned repository instead of the example function in the instructions. 

**OCI connector**
1. In the OCI portal, search for *Connectors*
2. Click *Create Connector*, give it a name and description.
3. Select *Logging* as the source and *Functions* as the target.
4. Under *Configure source* choose the log group and specific log that you want to stream to Dynatrace.
5. Under *Configure target* select your application and function created in the previous steps.
6. If you are prompted to create any policies, click on *Create*.
7. Finally click *Create* at the bottom of the panel, now you have a connector for streaming logs into Dynatrace. 