const {
  RESTDataSource
} = require('apollo-datasource-rest')

class BHLAPI extends RESTDataSource {
  constructor() {
    super();
    this.apiKey = '03343089-fc22-45f0-9417-32bd730f6edc'
    this.baseURL = 'https://www.biodiversitylibrary.org/'
  }

  async getNames(name) {
    let endpoint = 'api3?op=NameSearch' +
      '&name=' + name +
      '&apikey=' + this.apiKey +
      '&format=json'
    return this.get(endpoint);
  }

  async nameSearch(name) {
    let endpoint = "api3?op=GetNameMetadata" +
      '&name=' + name + '&searchtype=C' +
      '&apikey=' + this.apiKey +
      '&format=json'

    return this.get(endpoint);
  }

  async pageOCR(itemID) {
    let endpoint = 'pageocr/' + itemID
    return this.get(endpoint);
  }

  async getTitlePages(itemID) {
    let endpoint = 'api3?op=GetItemMetadata' +
      '&id=' + itemID +
      '&pages=t&ocr=t&parts=f' +
      '&apikey=' + this.apiKey +
      '&format=json'

    return this.get(endpoint);
  }

  async getTitleInfo(itemID) {
    let endpoint = 'api3?op=GetItemMetadata' +
      '&id=' + itemID +
      '&pages=f&ocr=f&parts=f' +
      '&apikey=' + this.apiKey +
      '&format=json'

    return this.get(endpoint);
  }
}

class EOLAPI extends RESTDataSource {
  constructor() {
    super()
    this.baseURL = 'http://eol.org/api/'
  }

  async getEntries(name) {
    let endpoint = 'search/1.0.json?q=' + name +
      '&page=1&exact=true'
    return this.get(endpoint)
  }

  async speciesAdditionalInfo(idSpecies) {
    let endpoint = 'pages/1.0.json?batch=false&id=' + idSpecies +
      '&subjects=overview&details=false&common_names=true' +
      '&synonyms=true&taxonomy=false'
    return this.get(endpoint)
  }
}

class SolR extends RESTDataSource {
  constructor() {
    super()
    this.baseURL = 'http://localhost:8985/solr/proposal/'
  }

  async getPars(species) {
    species = species.split(" ").length > 1 ? "%22" + species + "%22" : species

    let endpoint = 'select?fl=id,species,page_uri,doc_uri&q=species:' +
      species + '&rows=100&wt=json'

    return this.get(endpoint)
  }
}
module.exports = {
  BHLAPI: BHLAPI,
  EOLAPI: EOLAPI,
  SolR: SolR
}
