library(lbdatasets)

datasets <- ls("package:lbdatasets")
names(datasets) <- datasets


export_help <- function(x){
  ## dataset <- sprintf("lbdatasets::%s", x)
  ## csv_file <- sprintf("%s.csv", x)
  ## txt_file <- sprintf("%s.txt", x)
  # data
  ## write.csv(eval(parse(text = dataset)), file = csv_file, row.names = FALSE)
  ## # documentation l'help system non viene redirezionato allo stdout..
  ## sink(txt_file, type = c("output", "message"))
  help(x, package = "lbdatasets", help_type = "text")
  ## sink()
}



lapply(datasets,  export_help)

system("rm -rf .RData")
