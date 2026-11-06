"""Offline workspace provisioning. Credentials are shown once to the operator."""

import argparse
import os
from .identity import IdentityStore
from .store import Store


def main():
    parser = argparse.ArgumentParser(
        description="Provision or revoke pilot workspace access locally"
    )
    parser.add_argument(
        "--database", default=os.getenv("AGENT_DATABASE", ".agent-v3/tasks.sqlite3")
    )
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("provision")
    create.add_argument("--name", required=True)
    create.add_argument(
        "--role",
        choices=["master", "administrator", "user"],
        default="master",
    )
    create.add_argument(
        "--workspace", help="Existing workspace ID; omit to create a workspace"
    )
    revoke = commands.add_parser("revoke")
    revoke.add_argument("--key-id", required=True)
    args = parser.parse_args()
    identities = IdentityStore(Store(args.database))
    if args.command == "provision":
        identity, token = identities.provision(args.name, args.role, args.workspace)
        print("Workspace:", identity.workspace)
        print("Key ID:", identity.key_id)
        print("Role:", identity.role)
        print("Credential (store securely; shown once):", token)
    else:
        identities.revoke(args.key_id)
        print("Credential revoked")


if __name__ == "__main__":
    main()
