foodlog <- read.csv("food_logs.csv", header = FALSE)


head(foodlog)

summary(foodlog)
library(sqldf)
foodlogrem <- sqldf("select * from foodlog where V1 LIKE ',%'")
foodlogrem
foodlog <- foodlog[!(foodlog$V1 %in% foodlogrem$V1),]
nrow(foodlogrem)
nrow(foodlog)
summary(foodlog)
foodlog
foodlog <- foodlog[foodlog$V3=='Menu',]

foodlog <- subset(foodlog, select = -c(12))

colnames(foodlog)[colnames(foodlog)=="V1"] <- "id"
colnames(foodlog)[colnames(foodlog)=="V2"] <- "itemname"
colnames(foodlog)[colnames(foodlog)=="V3"] <- "itemtype"
colnames(foodlog)[colnames(foodlog)=="V4"] <- "datecreated"
colnames(foodlog)[colnames(foodlog)=="V5"] <- "datedumped"
colnames(foodlog)[colnames(foodlog)=="V6"] <- "mealtype"
colnames(foodlog)[colnames(foodlog)=="V7"] <- "actiontaken"
colnames(foodlog)[colnames(foodlog)=="V8"] <- "actionreason"
colnames(foodlog)[colnames(foodlog)=="V9"] <- "quantity"
colnames(foodlog)[colnames(foodlog)=="V10"] <- "quantitytype"
colnames(foodlog)[colnames(foodlog)=="V11"] <- "locationid"
summary(foodlog)
typeof(foodlog$locationid)
summary(foodlog$locationid)

write.csv(foodlog, file = "newfoodlog.csv")

newfoodlog <- read.csv("newfoodlog.csv")
summary(newfoodlog)

loc9foodlog <- newfoodlog[newfoodlog$locationid=='9',]
summary(loc9foodlog)
write.csv(loc9foodlog, file = "foodlogloc9.csv")
loc9foodlog <- read.csv("foodlogloc9.csv")
summary(loc9foodlog)
loc9foodlog$X.1 <- NULL
loc9foodlog$X <- NULL
loc9foodlog$itemtype <- NULL
loc9foodlog$datecreated <- NULL
loc9foodlog$locationid <- NULL
summary(loc9foodlog)

#action taken = Discarded and action Reason = Over production
loc9foodlog <- loc9foodlog[loc9foodlog$actiontaken=='Discarded',]
summary(loc9foodlog)
loc9foodlog <- loc9foodlog[loc9foodlog$actionreason=='Over Production',]
summary(loc9foodlog)

loc9foodlog$id <- NULL
summary(loc9foodlog)

#loc9foodlog$datedumped <- as.Date(loc9foodlog$datedumped , "%y-%m-%d")
summary(loc9foodlog)
typeof(loc9foodlog$datedumped)

loc9foodlog$datedumpednew <- as.Date(loc9foodlog$datedumped , "%Y-%m-%d")
summary(loc9foodlog)
typeof(loc9foodlog$datedumpednew)

d <- as.numeric(loc9foodlog$datedumpednew)
d
summary(d)
d <- d-16516
d
loc9foodlog$datesort <- d
summary(loc9foodlog)
loc9foodlog$X <-NULL
loc9foodlog$datedumped <-NULL
loc9foodlog$actiontaken <-NULL
loc9foodlog$actionreason <-NULL
loc9foodlog$datedumpednew <-NULL
summary(loc9foodlog)

loc9pound <- loc9foodlog[loc9foodlog$quantitytype=="Pound",]
summary(loc9pound)
write.csv(loc9pound, file = "loc9.csv")


loc9foodlog <- read.csv("loc9.csv")
summary(loc9foodlog)
loc9pound <- loc9foodlog[loc9foodlog$quantitytype=="Pound",]

summary(loc9pound)
nrow(loc9pound)
plot(loc9pound$quantity)

outlier_values <- boxplot.stats(loc9pound$quantity)$out  # outlier values.
boxplot(loc9pound$quantity, main="Quantity", boxwex=0.1)
mtext(paste("Outliers: ", paste(outlier_values, collapse=", ")), cex=0.6)

boxplot(quantity ~ datesort, data=loc9pound, main="X")  # clear pattern is noticeable.

# For continuous variable (convert to categorical if needed.)
boxplot(quantity ~ datesort, data=loc9pound, main="Boxplot ")
boxplot(quantity ~ cut(datesort, pretty(loc9pound$datesort)), data=loc9pound, main="Boxplot for categorical",
        cex.axis=0.5)

mod <- lm(quantity ~ mealtype+datesort, data=loc9pound)
cooksd <- cooks.distance(mod)
plot(cooksd, pch="*", cex=2, main="Influential Obs by Cooks distance")  # plot cook's distance
abline(h = 4*mean(cooksd, na.rm=T), col="red")  # add cutoff line
text(x=1:length(cooksd)+1, y=cooksd, labels=ifelse(cooksd>4*mean(cooksd, na.rm=T),names(cooksd),""),
     col="red")  # add labels
influential <- as.numeric(names(cooksd)[(cooksd > 4*mean(cooksd, na.rm=T))])  # influential row numbers
head(loc9pound[influential, ])  # influential observations.



x <- loc9pound$quantity
qnt <- quantile(x, probs=c(.25, .75), na.rm = T)
caps <- quantile(x, probs=c(.05, .95), na.rm = T)
caps
qnt
H <- 1.5 * IQR(x, na.rm = T)
H
median(loc9pound$quantity)
#x[x < (qnt[1] - H)] <- caps[1]
#x[x < (qnt[2] - H)]
x[x > (qnt[2] + H)] <- mean(loc9pound$quantity)
x
loc9pound$quantity <- x



summary(loc9pound)
unique(loc9pound$itemname)
loc9pound$itemid <- as.integer(loc9pound$itemname)
summary(loc9pound)

summary(loc9pound)
loc9pound$mealtypeid <- as.integer(loc9pound$mealtype)

set.seed(123)
sample = sample.split(loc9pound, SplitRatio = 0.80)
train = subset(loc9pound, sample == TRUE)
test  = subset(loc9pound, sample == FALSE)
summary(train)


#Linear Regression

modellm1 <- lm(quantity ~ datesort, data =train)
summary(modellm1)
predlm1 <- predict(modellm1, test)
summary(predlm1)
predlm1
rmselm1 <- rmse(test$quantity, predlm1)
rmselm1
difflm1 <- test$quantity-predlm1
summary(difflm1)



#Rpart

library(rpart)
modelrp1 <- rpart(quantity ~ datesort, data=train)
summary(modelrp1)
predrp1 <- predict(modelrp1,test)
summary(predrp1)
predrp1
rmserp1 <- rmse(test$quantity, predrp1)
rmserp1
diffrp1 <- test$quantity-predrp1
summary(diffrp1)



#Logistic Regression


modelglm1 <- glm(quantity ~ datesort , data=train)
summary(modelglm1)
predglm1 <- predict(modelglm1,test)
summary(predglm1)
predglm1
rmseglm1 <- rmse(test$quantity, predglm1)
rmseglm1
diffglm1 <- test$quantity-predglm1
summary(diffglm1)


#PCR
library(pls)


pcr1 <- pcr(quantity ~  datesort  , data = train, scale = TRUE, validation = "CV")
validationplot(pcr1, val.type = "MSEP")
predpcr1 <- predict(pcr1, test, ncomp = 1)
predpcr1
pcrrmse1 <- rmse(test$quantity, predpcr1)
pcrrmse1
diffpcr1 <- test$quantity-predpcr1
summary(diffpcr1)



#PLS

pls1 <- plsr(quantity ~  datesort  , data = train, scale = TRUE, validation = "CV")
validationplot(pls1, val.type = "MSEP")
predpls1 <- predict(pls1, test, ncomp = 1)
predpls1
plsrmse1 <- rmse(test$quantity, predpls1)
plsrmse1
diffpls1 <- test$quantity-predpls1
summary(diffpls1)












#Gradient Boosting Machine
library(gbm)


library(gbm)
gbmmodel1 <- gbm(quantity ~ datesort  ,data = train )
predgbm1 <- predict(gbmmodel1, n.trees = gbmmodel1$n.trees, test)
predgbm1
length(predgbm1)
gbmrmse1 <- rmse(test$quantity, predgbm1)
gbmrmse1
diffgbm1 <- test$quantity-predgbm1
summary(diffgbm1)




#SVM 
library(e1071)


svmmodel1 <- svm(quantity ~ datesort  ,data = train)
svmpred1 <- predict(svmmodel1, test)
points(test$quantity, svmpred1, col = "red", pch=4)
svmpred1
svmrmse1 <- rmse(test$quantity, svmpred1)
svmrmse1
diffsvm1 <- test$quantity-svmpred1
summary(diffsvm1)



# Random Forest  
set.seed(147)


fit = randomForest(quantity~ datesort , train, ntree = 501)
varImpPlot(fit)
predrf1 = predict(fit, test, type = "response")
predrf1
rfrmse1 <- rmse(test$quantity, predrf1)
rfrmse1
diffrf1 <- test$quantity-predrf1
summary(diffrf1)
predrf1
test$quantity
diffrf1
length(test$quantity)
length(predrf1)





rmselm1
rmserp1
rmseglm1
pcrrmse1
plsrmse1
gbmrmse1
svmrmse1
rfrmse1



summary(loc9pound$itemname)
loc9foodlog <- read.csv("loc9.csv")
summary(loc9foodlog)
loc9pound <- loc9foodlog[loc9foodlog$quantitytype=="Pound",]
summary(loc9pound)
unique(loc9pound$itemname)
loc9pound$itemid <- as.integer(loc9pound$itemname)
summary(loc9pound)

summary(loc9pound)
loc9pound$mealtypeid <- as.integer(loc9pound$mealtype)


a <- sqldf("select count(itemname) as cnt, itemname, itemid from loc9pound 
           group by itemname order by cnt desc")
summary(a)
a


data193 <- loc9pound[loc9pound$itemname=='193',]
summary(data193)

summary(loc9pound)
maxquant <- sqldf("select itemname, quantity, itemid, datesort from loc9pound
                  order by quantity desc")
head(maxquant)
maxquant

data199 <- loc9pound[loc9pound$itemid=='199',]
summary(data199)
write.csv(data199, file = "data199.csv")
data199 <- read.csv("data199.csv")
summary(data199)
set.seed(147)
library(MASS)
library(caTools)
sample = sample.split(data199, SplitRatio = 0.80)
train199 = subset(data199, sample == TRUE)
test199  = subset(data199, sample == FALSE)
summary(train199)
summary(test199)


#GBM
library(gbm)
gbmmodel199 <- gbm(quantity ~ datesort + mealtypeid ,data = train199 )
predgbm199 <- predict(gbmmodel199, n.trees = gbmmodel199$n.trees, test199)
predgbm199
length(predgbm199)
library(Metrics)
gbmrmse199 <- rmse(test199$quantity, predgbm199)
gbmrmse199
diffgbm199 <- test199$quantity-predgbm199
summary(diffgbm199)

# Random Forest  
set.seed(2019) 
library(randomForest)
fit199 = randomForest(quantity~ datesort + mealtypeid, train199, ntree =51)
varImpPlot(fit199)
predrf199 = predict(fit199, test199, type = "response")
predrf199
rfrmse199 <- rmse(test199$quantity, predrf199)
rfrmse199
diffrf199 <- test199$quantity-predrf199
summary(diffrf199)
predrf199
test199$quantity
diffrf199





write.csv(test199, file = "test199.csv")
summary(test199)
summary(train199)
testtry199 <- read.csv("testtry199.csv")
summary(testtry199)


trygbmmodel199 <- gbm(quantity ~ datesort + mealtypeid ,data = train199 )
trypredgbm199 <- predict(trygbmmodel199, n.trees = trygbmmodel199$n.trees, testtry199)
trypredgbm199


# Random Forest  
set.seed(123) 
fit199 = randomForest(quantity~ datesort + mealtypeid, train199, ntree =21)
varImpPlot(fit199)
trypredrf199 = predict(fit199, testtry199, type = "response")
trypredrf199
head(test199)
summary(train199)
summary(diffrf199)
#6 dollars per pound

