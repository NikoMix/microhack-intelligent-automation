# Contoso VPN Setup

## Prerequisites
Users need an active Entra ID account, Microsoft Authenticator registration, and a managed device enrolled in Intune. Contractors must have a sponsor-approved access request before VPN access is enabled.

## Setup Steps
Install the Contoso VPN client from Company Portal, open the client, choose the Europe profile, and sign in with Entra ID. Approve the multifactor prompt in Microsoft Authenticator. The client shows Connected when the tunnel is ready.

## Troubleshooting
If sign-in loops, confirm the device is compliant in Company Portal and retry after 15 minutes. If the Europe profile is missing, sync Company Portal and reinstall the VPN profile package.
