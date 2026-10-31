import anthropic
from anthropic import WorkloadIdentityCredentials

language = "vi"
def fetch_identity_token() -> str:
    # However your platform exposes its OIDC identity token.
    raise NotImplementedError

client = anthropic.Anthropic(
    credentials=WorkloadIdentityCredentials(
        identity_token_provider=fetch_identity_token,
        federation_rule_id="fdrl_01WQRHPumxZ6oeZUh8DiG8cr",
        organization_id="68a920ea-774b-45cd-b650-01186bfce58c",
        service_account_id="svac_01AeDWrusvi1GSm3H44agmxu",
        workspace_id="wrkspc_01B1rno8jwvAtekvj7sUPATu",
    ),
)

message = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello, Claude"}],
)
print(next(block.text for block in message.content if block.type == "text"))