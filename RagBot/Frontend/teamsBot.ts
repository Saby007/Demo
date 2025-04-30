import { TeamsActivityHandler, TurnContext } from "botbuilder";
import axios from "axios";

export class TeamsBot extends TeamsActivityHandler {
  constructor() {
    super();
    this.onMessage(async (context, next) => {
      console.log("Running with Message Activity.");

      const removedMentionText = TurnContext.removeRecipientMention(context.activity);
      const userQuery = removedMentionText.toLowerCase().replace(/\n|\r/g, "").trim();

      // Send "Processing..." message
      const processingMessage = await context.sendActivity("Processing .......");

      try {
        // Make POST request to the backend
        const response = await axios.post(
          "https://demowebappbackend-e9asb4gtbrb5f5az.eastus2-01.azurewebsites.net/process",
          {
            user_query: userQuery,
          }
        );

        // Extract the output string from the response
        const outputString = response.data.output_string;

        // Send the response back to the user
        await context.updateActivity({
          id: processingMessage.id,
          type: "message",
          text: outputString,
        });
      } catch (error) {
        console.error("Error while processing the query:", error);
        await context.updateActivity({
          id: processingMessage.id,
          type: "message",
          text: "Sorry, something went wrong while processing your request.",
        });
      }

      // By calling next() you ensure that the next BotHandler is run.
      await next();
    });

    this.onMembersAdded(async (context, next) => {
      const membersAdded = context.activity.membersAdded;
      for (let cnt = 0; cnt < membersAdded.length; cnt++) {
        if (membersAdded[cnt].id) {
          await context.sendActivity(
            `Hi there! I'm a Teams bot that will process your queries.`
          );
          break;
        }
      }
      await next();
    });
  }
}