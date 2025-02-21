import autogen
from autogen.agentchat.contrib.multimodal_conversable_agent import MultimodalConversableAgent

from pdf_reports import pug_to_html, write_report
import ast

config_list = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    filter_dict={
        "model": ["gpt-4-vision-preview"],
    },
)
llm_config = {
    "config_list": config_list,
    "seed": 33,  # change the seed for different trials

}

[config.pop("api_type", None) for config in config_list]

chatbot = MultimodalConversableAgent(
    name="chatbot",
    system_message="Do a thread modeling exercise is complete, add the executive summary, table, and long-form write-up to the report. Only use the functions you have been provided with. Make sure the executive summary starts with 'Executive Summary:'. The sumary should identify the top 3 priorities, and be no more than 220 words. The details should be a list of lists of the form '[[component, threat, mitigation], [component, threat, mitigation], ...] Reply TERMINATE when the task is done.",
    llm_config=llm_config,
)

# create a UserProxyAgent instance named "user_proxy"
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    code_execution_config={"work_dir": "coding"},
)

# define functions according to the function desription

def exec_python(cell, details, longform):
    print(longform)

    pug_template_string = """img(style="width:200px; display:block; margin:0 auto; opacity:1;" src="file:///Users/jeffreyjeyachandren/Desktop/threat-modeling-agents/threat-modeling-agents/threat_agents_team.svg")
#sidebar

.ui.stacked.segment.inverted.grey: p.
  This is an auto-generated Threat Modeling Report, assembled by GPT-4 Threat Modeling Agents. 
  The system reviews the specified application architecture. 
  It applies the STRIDE methodology to each component, providing a thorough evaluation of potential security threats, but may still contain errors.
  
.ui.container
  .ui.icon.message.blue.block-center
    i.exclamation.circle.icon
    .content
      .header Executive Summary
      p.
        {{ important_message_body }}

:markdown
  ##  Results
table.ui.celled.table
  thead
    tr
      th Component
      th Threats
      th Mitigations
  tbody
      {{ table_rows }}

:markdown
    ##  Discussion
    {{ longform }}
      
      """


    #print("/n/n details: ", details)

    # Strip quotes from the beginning and end of the string
    s = cell.strip('"\'')
    while s.startswith('#'):
        s = s[1:].strip()
    
    # Check if the string starts with 'Executive Summary' and remove it
    exec_summ_prefix = 'Executive Summary:'
    if s.startswith(exec_summ_prefix):
        # Slice the string to remove the 'Executive Summary' part
        s = s[len(exec_summ_prefix):].strip()

    important_message_body = s
    table_rows = generate_pug_table_rows(details)
    pug_with_table = pug_template_string.replace("{{ table_rows }}", table_rows)

    #print(pug_with_table)

    # Pass the variables to the Pug template
    html = pug_to_html(string=pug_with_table, 
                       important_message_body=important_message_body,
                       longform=longform,
                       )

    # Generate the report
    write_report(html, "stride_report.pdf")

def generate_pug_table_rows(data):
    pug_rows = []
    data_list = ast.literal_eval(data)

    for row in data_list:
        #print("\n\nrow: ", row)
        # Start a new row
        pug_row = "  tr\n"
        
        # Add each cell in the row
        for cell in row:
            #print("\nitem in row: ", cell)
            pug_row += f"  td {cell}\n"
        
        pug_rows.append(pug_row)
    
    return "\n".join(pug_rows)

def exec_sh(script):
    return user_proxy.execute_code_blocks([("sh", script)])

# register the functions
user_proxy.register_function(
    function_map={
        "python": exec_python    
        }
)

# start the conversation
user_proxy.initiate_chat(
    chatbot,
    message="Perform a threat modeling exercise on the app architecture that identifies all app components, STRIDE threats on each component, and mitigations for each STRIDE Threat. App architecture: <img https://raw.githubusercontent.com/JeffinWithYa/threat-modeling-agents/main/tm/dfd.png>",
)

