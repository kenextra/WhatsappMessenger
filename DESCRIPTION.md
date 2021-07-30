## Project name: *__Climate Messenger__*

## Short Description:
Whatsapp-based bot, for agriculture news, price prediction and search options.

[Github Repository](https://github.com/kenextra/WhatsappMessenger)

[Link to 3 minutes video](https://www.youtube.com/watch?v=lP_gNI73KBU&ab_channel=KenechukwuNnodu)


## Long Description:
### Problem statement:
Approximately 9 percent of the global population is suffering from hunger. And, much of the world’s food is grown by small-scale, independent farms and distributed through local community cooperatives who sell the surplus produce. These independent farmers and co-ops do not have accessible tools/platforms to get the right information for better crop production and price fairness. 

In addition, communities and policy makers require collective efforts to  gather and disseminate  relevant data of climate trends in order to derive insights, provide recommendations in record time. 

### Solution:
By leveraging on the popularity and accessibility of WhatsApp and Twilio APIs, a researcher can easily access verified updates on environmental trends and scientific breakthroughs; derive insights and provide recommendations to communities and policy makers  in real-time through the development of an  easy-to-use, WhatsApp-based, interactive messaging chatbot, with the potential to reach over 2 billion people, and lead international efforts at delivering real-time information on sustainable, inclusive and equitable development on food, agriculture and environment, directly into the hands of the people that need it for better decision making;  from food price prediction in international markets, to news about socio economic and political factors of crop production,  food distribution, food prices, environmental laws, to  information about for actionable insights  for possible reduction of post-harvest losses and lots more solutions. 

Easy access to the latest situation reports about climate change and better adaptation measures to real-time environmental, University research updates  on modern conservation of natural resources  could help government decision-makers  to effectively address hunger in rural communities, conserve natural resources while curtailing the effects of climate change. 

Our solution leverages on the diversity of WhatsApp's reach and  is accessibility to those who have limited data and  limited storage spaces for new app downloads on their phones as such, they don't need to make an extra app-space for this service. 

The WhatsApp based messaging service for real-time access to information about Food and Agriculture was  developed with open source repositories and food producer prices data of the Food and Agricultural Organisation, using  machine learning technology in Watson studio deployed on IBM cloud foundry. 

## IBM Technologies used:
- [IBM Cloud Foundry](https://cloud.ibm.com/catalog?search=cloud%20foundry#search_results) - The compute platform used for creating and deploying applications
- [Watson Machine Learning](https://cloud.ibm.com/catalog?search=machine%20learning#search_results) - Uesd to build the ML model
- [Watson Studio](https://cloud.ibm.com/catalog?search=studio#search_results) - Uesd to deploy the ML model.
- [Object Storage](https://cloud.ibm.com/catalog?search=object%20storage#search_results) - Used to store ML Model and artifacts

## Programming Languages used:
- Python Programming Language.


## Other Affiliate Technologies:
- [Twilio Messaging API](https://www.twilio.com/) - Programmable Messaging service used


## Dataset Used:
[Food producer prices data](http://www.fao.org/faostat/en/#data):

Agriculture Producer Prices are prices received by farmers for primary crops, live animals and livestock primary products as collected at the point of initial sale (prices paid at the farm-gate).
Annual data are provided from 1991, while mothly data from January 2010 for 180 country and 212 product.

For our purpose we chose 10 popular products found in developing and developed countries and as a result we a total 117 countries.

The popular products selected are:
- Potatoes
- Maize
- Wheat
- Apples
- Rice
- Soybeans
- Sweet potatoes
- Cassava
- Sorghum
- Yams
- Plantains


## Work Flow Diagram:
<!--add an image in this path-->
![architecture](doc/source/images/architecture.png)

<!--Add flow steps based on the architecture diagram-->
## Flow

1. User sends a message through WhatsApp.

2. The message is redirected to Twilio Programmable Messaging service.

3. Twilio Programmable Messaging service will further forward the message to the framework hosted on IBM Cloud.

4. The framework interacts with one of the Watson Machine Learning to get the response.

5. The Watson Machine Learning does the necessary computation and returns a response accordingly.

6. The framework processes the response and converts it to user readable format and forwards it Twilio.

7. Twilio forwards this message as a reply on WhatsApp.

8. The user will receive this as a response from Watson service on WhatsApp.


## Our Solution Road Map:
See below for our proposed schedule on next steps after Call for Code 2021 submission.

See [ROADMAP.md](ROADMAP.md)
