{
  "config": {
    "step": {
      "user": {
        "title": "SpotScheduler",
        "description": "Konfiguroi SpotScheduler ohjaamaan laitteita Nord Pool pörssisähkön hintojen mukaan.\n\nVaatii sisäänrakennetun Nord Pool -integraation (Home Assistant 2024.12+).",
        "data": {
          "name": "Nimi",
          "nordpool_config_entry": "Nord Pool -integraatio",
          "expensive_hours_count": "Kalliiden tuntien korostus"
        },
        "data_description": {
          "nordpool_config_entry": "Valitse konfiguroitu Nord Pool -integraatiosi.",
          "expensive_hours_count": "Tämä määrä kalleimpia tunteja korostetaan punaisella aikataulunäkymässä."
        }
      },
      "devices": {
        "title": "Valitse laitteet",
        "description": "Valitse ohjattavat laitteet. Tuetut tyypit: kytkimet, valot, termostaatit, input_boolean.",
        "data": {
          "devices": "Ohjattavat laitteet"
        }
      }
    },
    "error": {
      "no_devices_selected": "Valitse vähintään yksi laite."
    },
    "abort": {
      "nordpool_not_found": "Nord Pool -integraatiota ei löydy. Asenna se ensin kohdasta Asetukset → Laitteet ja palvelut."
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "SpotScheduler – asetukset",
        "data": {
          "devices": "Ohjattavat laitteet",
          "expensive_hours_count": "Kalliiden tuntien korostus"
        },
        "data_description": {
          "devices": "Lisää tai poista laitteita aikataulusta.",
          "expensive_hours_count": "Tämä määrä kalleimpia tunteja korostetaan punaisella aikataulunäkymässä."
        }
      }
    }
  },
  "issues": {
    "nordpool_integration_missing": {
      "title": "Nord Pool -integraatio poistettu",
      "description": "SpotSchedulerin käyttämää Nord Pool -integraatiota ei enää löydy. Lisää Nord Pool uudelleen kohdasta Asetukset → Laitteet ja palvelut, ja käynnistä SpotScheduler uudelleen."
    },
    "nordpool_unavailable": {
      "title": "Nord Pool -hinnat eivät saatavilla",
      "description": "SpotScheduler ei saanut päivän sähköhintoja. Nord Pool API saattaa olla tilapäisesti alhaalla. Hintojen haku yritetään automaattisesti uudelleen.\n\nVoit myös pakottaa päivityksen: **Palvelut → spot_scheduler.refresh_prices**."
    }
  }
}
