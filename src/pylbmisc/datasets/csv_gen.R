library(lbdatasets)

lapply(ls("package:lbdatasets"), function(x){
  dataset = sprintf("lbdatasets::%s", x)
  file = sprintf("%s.csv", x)
  write.csv(eval(parse(text = dataset)), file = file, row.names = FALSE)
})
