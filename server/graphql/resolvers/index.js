module.exports = {
  Query: {
    // Users
    names: (async (_, {
      name
    }, {
      dataSources
    }) => {
      let names = await dataSources.bhlAPI.getNames(name)
      names = names.Result
      return names.map(x => x.NameConfirmed)
    }),

    nameResults: (async (_, {
      name
    }, {
      dataSources
    }) => {
      let results = await dataSources.bhlAPI.nameSearch(name)
      results = results.Result[0]

      if (results == null)
        return null


      let titles = results.Titles.map(x => {
        // Just for proposal we select just first volume
        // We have to decide how to choose between volumes
        // Most of time is same book but differetn year
        let pages = x.Items[0].Pages.map(p => {
          return {
            ItemID: p.ItemID,
            PageID: p.PageID,
            PageUrl: p.PageUrl,
            OcrUrl: p.OcrUrl,
            TextOCR: p.OcrUrl.split("/")
          }
        })

        return {
          ItemUrl: x.Items[0].ItemUrl,
          Pages: pages
        }
      })

      return [{
        name: results.NameConfirmed,
        titles: titles
      }]
    }),


    title: (async (_, {
      id
    }, {
      dataSources
    }) => {
      let title = await dataSources.bhlAPI.getTitlePages(id)

      // Just for proposal we select just first volume
      // We have to decide how to choose between volumes
      // Most of time is same book but differetn year
      title = title.Result[0]

      let pages = title.Pages.map((p) => {
        return {
          ItemID: p.ItemID,
          PageID: p.PageID,
          PageUrl: p.PageUrl,
          OcrUrl: p.OcrUrl,
          TextOCR: p.OcrText,
        }
      })

      return {
        TitleUrl: title.TitleUrl,
        ItemUrl: title.ItemUrl,
        Pages: pages
      }
    }),

    entries: (async (_, {
      name
    }, {
      dataSources
    }) => {
      let entries = await dataSources.eolAPI.getEntries(name)
      entries = entries.results

      entries = entries.map((x) => {
        return {
          id: x.id,
          title: x.title,
          content: x.content,
          additionalInfo: x.id
        }
      })

      return entries
    }),

    paragraphs: (async (_, {
      species
    }, {
      dataSources
    }) => {
      let res = await dataSources.solR.getPars(species)

      paragraphs = JSON.parse(res).response.docs

      return paragraphs
    })
  },

  TextOCRd: {
    text: async (text, args, {
      dataSources
    }) => {
      let textOCRd = text
      try {
        let ocrID = text.pop()
        textOCRd = await dataSources.bhlAPI.pageOCR(ocrID)
      } catch {
        // When we are here, it means that text is
        // already OCRD
      }

      return textOCRd
    }
  },

  Info: {
    info: async (id, args, {
      dataSources
    }) => {
      let results = await dataSources.eolAPI.speciesAdditionalInfo(id)

      return {
        synonyms: results.synonyms.map(s => s.synonym),
        vernacularNames: results.vernacularNames.map(s => s.vernacularName),
      }
    }
  },

  Title: {
    TitleInfo: async (title, args, {
      dataSources
    }) => {
      let id = title.ItemUrl.split("/").pop()
      let res = await dataSources.bhlAPI.getTitleInfo(id)
      res = res.Result[0]

      return {
        institution: res.HoldingInstitution,
        lang: res.Language,
        year: res.Year,
        vol: res.Volume
      }
    }
  }
}
