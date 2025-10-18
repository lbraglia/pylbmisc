library(lbdatasets)

datasets <- ls("package:lbdatasets")

export_data <- function(x){
  dataset <- sprintf("lbdatasets::%s", x)
  csv_file <- sprintf("%s.csv", x)
  txt_file <- sprintf("%s.txt", x)
  # data
  write.csv(eval(parse(text = dataset)), file = csv_file, row.names = FALSE)
  # documentation
  sink(txt_file)
  help(x, package = "lbdatasets", help_type = "text")
  sink()
}

lapply(datasets,  export_data)

system("rm -rf .RData")
