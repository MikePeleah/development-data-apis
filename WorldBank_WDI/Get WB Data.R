#################################################################################################################
##
## Script for getting data from the WorldBank using API 
## API Documentation https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures
## GitHub https://github.com/MikePeleah/development-data-apis
## For comments and suggestions Mike.Peleah@gmail.com
##
#################################################################################################################
library(dplyr)
library(jsonlite)
library(httr)
library(tidyr)

# Set working directory 
setwd("Q:\\SDG Update")
# Load list of series and list of countries from files
cntrs <- read.csv(file="wb-cntry.csv", stringsAsFactors = FALSE)
inds <- read.csv(file="wb-series.csv", stringsAsFactors = FALSE)
# Time frame for data
t <- "1998:2019"
first.run <- TRUE
loc <- paste(c(cntrs$country.code), collapse=";")

for (i in inds$series.id) {
  # Generate URL for data reequest
  req <- paste("http://api.worldbank.org/v2/country/", loc, "/indicator/", i, "?date=", t, "&per_page=4096&format=json", sep="")
  print(paste0("> Processing ", i))
  g <- GET(url=req)
  r <- content(g, "text")
  tryCatch({
    d <- as.data.frame(fromJSON(r)[2])
    d2 <- data.frame(d$indicator$id, d$country$id, d$countryiso3code, as.numeric(d$date), d$value, stringsAsFactors=FALSE) %>% filter(!is.na(d.value))
    colnames(d2) <- c("series.id", "country.id", "country.code", "year", "value")
    write.table(d2, file=paste0(".\\Data-WB\\",i,".csv"), append = FALSE, col.names=TRUE, row.names = FALSE, sep=",")
    first.run <- FALSE
    log.str=paste("Got ",i, sep=" ")
    write(log.str, file="WB-WDI.log", append=TRUE)
  }, error=function(error_message) {
    message("Ooops, something went wrong for series ", i)
    message(error_message)
    log.str=paste("Problem with ",i, sep=" ")
    write(r, file=paste0(i,"-RAW.txt", append=FALSE))
    write(log.str, file="WB-WDI.log", append=TRUE)
    return(NA)
  })
  print(paste0("  ", log.str))
}
