# If you not install nvm and node.js, please run the following commands:
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
nvm install --lts
nvm use --lts

npm init -y
npm install express cors bcryptjs jsonwebtoken axios
node server.js