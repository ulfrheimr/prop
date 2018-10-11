const {
  gql
} = require('apollo-server-express')

const a = gql `
  type Query {
    names(name:String!): [String]
    nameResults(name: String): [NameResult]
    title(id:ID!): Title
    entries(name: String!): [Entry]

    paragraphs(species:String!): [ParagraphResult]
  }

  type NameResult{
    name: String
    titles: [Title]
  }

  type Title{
    ItemUrl: String
    TitleInfo: TitleInfo
    Pages: [Page]
  }

  type Page{
    ItemID: String!
    PageID: String!
    PageUrl: String!
    OcrUrl: String!
    TextOCR: TextOCRd

  }

  type TextOCRd{
    text: String
  }

  type Entry{
    id: ID!
    title: String!
    content: String!
    additionalInfo: Info
  }

  type Info{
    info: Additional
  }

  type Additional{
    synonyms: [String]
    vernacularNames: [String]
  }

  type TitleInfo{
    institution: String
    lang: String
    year: String
    vol: String
  }

  # SOLR STUFF
  type ParagraphResult{
    id: ID!
    species: String!
    page_uri: [String]
    doc_uri: String
  }

`;

module.exports = a
