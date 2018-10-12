const express = require('express')
const cors = require('cors')
const {
  ApolloServer,
  gql
} = require('apollo-server-express')

const app = express();

const models = require("./models")
const resolvers = require('./resolvers')
const schema = require('./schema')
const dataSources = require('./data_sources')

const server = new ApolloServer({
  typeDefs: schema,
  resolvers,
  dataSources: () => {
    return {
      bhlAPI: new dataSources.BHLAPI(),
      eolAPI: new dataSources.EOLAPI(),
      solR: new dataSources.SolR()
    };
  },
  context: {

  },
});

server.applyMiddleware({
  app,
  path: '/graphql'
});

app.listen({
  port: 4002
}, () => {
  console.log('Apollo Server on http://localhost:4001/graphql');
});
