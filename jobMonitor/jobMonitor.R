#!/usr/bin/env Rscript

################################################
## Generates Overview Stats for Cluster Queue ##
################################################

## (1) Import jobs
jobImport <- function(cmd="module load slurm/19.05.0; sacct --delimiter '|' --parsable2 --allusers --format User,JobID,JobName,Partition,NodeList,Start,Elapsed,Timelimit,MaxRSS,State,AllocGRES,AllocTRES") {
    myjobs <- read.csv(text=suppressWarnings(system(cmd, intern=TRUE)), header=TRUE, sep="|") 
	return(myjobs)
}

## (2) Function to Import User Database (located at end of script)
importUserDB <- function(mycol=1:7) {
	userdb <- read.delim("/opt/linux/centos/7.x/x86_64/pkgs/hpcc_user_utils/user_utils/cache/user_details.txt")[ , mycol]
    userdb[,1] <- ifelse(as.vector(userdb[,1]), 1, 0)
    colnames(userdb)[1:7] <- c("FreqUser", "User_Name","Account_Name","User_Email", "PI_Name", "PI_Email", "Department")
	return(userdb)
}

## (3) Stats function for job resources
clusterStats <- function(input=myjobList) {
    library(stringr)
	nodenames <- lapply(input$NodeList, function(x) { gsub("^None.*", NA, x) }) # assigns NA to empty components
    Ncores <- lapply(str_split_fixed(input$AllocTRES,',',3)[,1], function(x) { as.integer(gsub('cpu=','',x)) })
    Ncores[is.na(Ncores)] <- 0
    Nprocesses <- Ncores
	
	owner <- input$User
	owner <- lapply(owner, function(x) if(length(x)!=0) { x } else { NA } ) # assigns NA to empty components
	
	status <- input$State
	status <- lapply(status, function(x) if(length(x)!=0) { x } else { NA } ) # assigns NA to empty components	
	
	mem <- lapply(str_split_fixed(input$AllocTRES,',',3)[,2], function(x) {
	    if(length(x)!=0) {
            if ( length(grep('^mem=[0-9]*M$',x))!=0 ) {
                return(round(as.integer(gsub('M$', "", gsub('^mem=','',x,)))/1024))
            } else {
                return(as.integer(gsub('G$', "", gsub('^mem=','',x,))))
            }
        } else { return(NA) }  # assigns NA to empty components	        
    })

	statsDF <- data.frame(Owner=unlist(owner), Nodes=unlist(nodenames), N_Processes=unlist(Nprocesses), Status=unlist(status), GB_RAM=unlist(mem))
	return(statsDF)
}

## (4) Available nodes (provides info as what nodes are up or down)
nodesUp <- function() {	
	allnodenames <- as.character(read.delim("/opt/linux/centos/7.x/x86_64/pkgs/hpcc_user_utils/jobMonitor/cluster.conf")[,"Node_ID"])
    myconnection <- pipe('module load slurm/19.05.0; sinfo -N -o "%N %t"')
	if(length(readLines(myconnection))>0) { # Added on 20-Dec-12
		nonavailnodes <- read.table(myconnection)
		nonavailnodes <- sort(as.character(nonavailnodes[grep("drain|down|failed", nonavailnodes[,2], perl=TRUE),1]))
		nonavailnodes <- nonavailnodes[grep("\\d\\d$", nonavailnodes)]
		availNodes <- allnodenames[!allnodenames %in% nonavailnodes] 
	} else {
		availNodes <- allnodenames
		close(myconnection)
	}
	return(availNodes)
}

## (5) Run everything from statsReport function 
statsReport <- function(refresh=TRUE, plot="png", stdout=TRUE, tmpfile='', ...) {
	## Refresh job list
	if(refresh==TRUE) {
		myjobList <- jobImport()
		statsDF <- clusterStats(input=myjobList)
	    statsRunning <- statsDF[statsDF$Status=="RUNNING",] # Ignore queued jobs for memory calculations
	}
	## Import user database
	userdb <- importUserDB()
	## User run stats
	cluster_conf <- read.delim("/opt/linux/centos/7.x/x86_64/pkgs/hpcc_user_utils/jobMonitor/cluster.conf")
	cluster_conf_v <- as.character(cluster_conf$Queue); names(cluster_conf_v) <- as.character(cluster_conf$Node_ID)
    statsDFintel <- statsRunning[gsub("/.*", "", statsRunning$Nodes) %in% names(cluster_conf_v[cluster_conf_v == "intel"]),] # intel processes
    statsDFshort <- statsRunning[gsub("/.*", "", statsRunning$Nodes) %in% names(cluster_conf_v[cluster_conf_v == "short"]),] # intel processes
    statsDFbatch <- statsRunning[gsub("/.*", "", statsRunning$Nodes) %in% names(cluster_conf_v[cluster_conf_v == "batch"]),] # batch processes
	statsDFhighmem <- statsDF[gsub("/.*", "", statsDF$Nodes) %in% names(cluster_conf_v[cluster_conf_v == "highmem"]),] # highmem processes

	userStatsIntel <- tapply(statsDFintel$N_Processes, statsDFintel$Owner, sum)
	userStatsIntel[is.na(userStatsIntel)] <- 0
	
    userStatsShort <- tapply(statsDFshort$N_Processes, statsDFshort$Owner, sum)
	userStatsShort[is.na(userStatsShort)] <- 0

	userStats <- tapply(statsDFbatch$N_Processes, statsDFbatch$Owner, sum)
	userStats[is.na(userStats)] <- 0

	userStatshighmem <- tapply(statsDFhighmem$N_Processes, statsDFhighmem$Owner, sum)
	userStatshighmem[is.na(userStatshighmem)] <- 0

	userMem <- tapply(statsRunning$GB_RAM, statsRunning$Owner, sum, na.rm=TRUE)
	userMem[userMem==0] <- NA

	userStats <- data.frame(User=names(userStats), CoresIntel=as.vector(userStatsIntel), CoresShort=as.vector(userStatsShort), CoresBatch=as.vector(userStats), CoresHighmem=as.vector(userStatshighmem), GB_RAM=as.vector(userMem))
	userStats <- merge(userStats, userdb, by.x="User", by.y="Account_Name", all.x=T)
	userStats <- userStats[,-7] # Drop the 7th column FreqUser, I guess we dont need it

	## User waiting stats
	waitingStats <- statsDF
	waitingStats[,4] <- factor(waitingStats[,4], levels=c("RUNNING", "PENDING", "SUSPENDED", "COMPLETED", "CANCELLED", "FAILED", "TIMEOUT", "NODE_FAIL")) # this way there are always H and Q columns in data set
	waitingStats <- t(as.data.frame(sapply(unique(waitingStats$Owner), function(x) {subwait <- waitingStats[waitingStats[,1]==x,]
				tapply(subwait$Status, subwait$Status, length)})))
	rownames(waitingStats) <- unique(statsDF$Owner)
	waitingStats <- waitingStats[order(rownames(waitingStats)), , drop=FALSE]
	waitingStats[is.na(waitingStats)] <- 0
	waitingStats <- t(waitingStats)
	waitingStats["RUNNING",] <- 0 # sets running jobs to zero; this way it will allways ignore them in the plot and data container is never empty. 
	
	## Node stats
    nodestats <- tapply(statsRunning$N_Processes, statsRunning$Nodes, sum, na.rm=TRUE)
    nodememstats <- tapply(statsRunning$GB_RAM, statsRunning$Nodes, sum, na.rm=TRUE)
	cluster_conf <- read.delim("/opt/linux/centos/7.x/x86_64/pkgs/hpcc_user_utils/jobMonitor/cluster.conf")
	allnodes <- as.numeric(cluster_conf$N_cores); names(allnodes) <- as.character(cluster_conf$Node_ID)
    nodestats <- data.frame(Node_No=names(allnodes), Cores_Used=nodestats[names(allnodes)], GB_RAM=nodememstats[names(allnodes)])
    nodestats[is.na(nodestats$Cores_Used), "Cores_Used"] <- 0

    userfornodes <- tapply(statsRunning$Owner, statsRunning$Nodes, function(x) paste(unique(x), collapse=", "))
    nodestats <- data.frame(nodestats, Users=userfornodes[as.character(nodestats$Node_No)])

	nodestats[is.na(nodestats$Users), 3] <- 0
	nodesAvailable <- nodesUp() # Next three lines are there to inlclude info of nodes that are currently down.
	tmpcol <- nodestats[,2]; tmpcol[!nodestats[,1] %in% nodesAvailable] <- NA
    nodestats[,2] <- tmpcol

	## Final stats list containing everything
	statslist <- list(user=userStats[, c(1:3,4:length(userStats))], waiting=t(waitingStats)[,-1,drop=FALSE], nodes=nodestats, statsDF=statsDF)
	activityStats <- data.frame(Capacity=allnodes, Used=statslist$nodes[,2], Mem_Used=statslist$nodes[,3])
	activityStatsIntel <- activityStats[rownames(activityStats) %in% names(cluster_conf_v[cluster_conf_v == "intel"]),]
	activityStatsShort <- activityStats[rownames(activityStats) %in% names(cluster_conf_v[cluster_conf_v == "short"]),]
	activityStatsBatch <- activityStats[rownames(activityStats) %in% names(cluster_conf_v[cluster_conf_v == "batch"]),]
	activityStatsGpu <- activityStats[rownames(activityStats) %in% names(cluster_conf_v[cluster_conf_v == "gpu"]),]
	activityStatsHighmem <- activityStats[rownames(activityStats) %in% names(cluster_conf_v[cluster_conf_v == "highmem"]),]
	activityStatsHighmem[is.na(activityStatsHighmem$Mem_Used), "Mem_Used"] <- 0
    ## Print summary stats to screen 
	if(stdout==TRUE) {
		cat("\nMonitoring Report Created on: ", date(), "\n")
		# frequser <- paste(userdb[userdb$FreqUser==1,2], " <", userdb[userdb$FreqUser==1,4], ">, ", sep="", collapse="")
		# cat("\nFrequent User Email List: \n", frequser) # Includes all users with 1 in first column of User Database at the end of this script.
		cat("\n\nCores Busy on Nodes: \n\n")
		print(statslist$nodes)
		cat("\nNumber of CPU Cores Occupied by Users: \n\n")
		print(statslist$user)
		cat("\nJobs history with status Pending, Held, Failed, etc.: \n\n")
		print(statslist$waiting)
		cat("\nThere are", length(as.vector(na.omit(statslist$nodes[statslist$nodes$Cores_Used==0,1]))), "Entirely Idle Nodes:", as.vector(na.omit(statslist$nodes[statslist$nodes$Cores_Used==0,1])), "\n")
		cat("\nThere are", length(statslist$nodes[is.na(statslist$nodes[,2]), 2]), "Nodes Down:", as.vector(statslist$nodes[is.na(statslist$nodes[,2]), 1]), "\n")
		cat("\nCPU Cores Idle on Batch Queue: ", sum(activityStatsBatch$Capacity) - sum(activityStatsBatch[is.na(activityStatsBatch$Used),"Capacity"]) - sum(activityStatsBatch$Used, na.rm=TRUE), "\n")
	    cat("\nRAM Available on Highmem Nodes: ", paste(rownames(activityStatsHighmem), ": ", c(512, 512, 256) - activityStatsHighmem$Mem_Used, "GB, ", sep=""), "\n\n")
	}
	## Plot summary stats
    configGraph <- function (margins=TRUE){
        if (margins != TRUE) { par(mar=c(1,1,1,1)) }
        nf <- layout(matrix(c(1,1,1,2,2,2,3,4,5,6,6,6,7,7,7,8,8,8), 6, 3, byrow=TRUE), c(14,3.5,3.5), c(3.5,3.5,3.5,3.5,3.5,3.5), respect=TRUE)
        barplot(activityStatsIntel$Used, ylim=c(0,70), names.arg=names(cluster_conf_v[cluster_conf_v == "intel"]), col="gold", main=paste0("CPU Cores Busy on Nodes of Partition: Intel ", rownames(activityStatsIntel)[1], "-", rownames(activityStatsIntel)[length(activityStatsIntel[,1])]))
        #barplot(activityStatsShort$Used, ylim=c(0,70), names.arg=names(cluster_conf_v[cluster_conf_v == "short"]), col="orange", main=paste0("Short ", rownames(activityStatsShort)[1], "-", rownames(activityStatsShort)[length(activityStatsShort[,1])]))
        
        mydf <- rbind(activityStatsIntel,activityStatsShort)
        foo <- setNames(cbind(rownames(mydf), mydf, row.names = NULL), c("Node_Name", "Capacity", "Used", "Mem_Used"))
        activityStatsIntelShort <- foo[order(foo$Node_Name),]

        barplot(activityStatsIntelShort$Used, ylim=c(0,70), names.arg=sort(c(names(cluster_conf_v[cluster_conf_v == "short"]), names(cluster_conf_v[cluster_conf_v == "intel"]))), col="orange", main="Short"  )
        barplot(activityStatsBatch$Used, ylim=c(0,70), names.arg=names(cluster_conf_v[cluster_conf_v == "batch"]), col="green", main=paste0("Batch ", rownames(activityStatsBatch)[1], "-", rownames(activityStatsBatch)[length(activityStatsBatch[,1])]))
        barplot(activityStatsHighmem$Used, ylim=c(0,70), names.arg=names(cluster_conf_v[cluster_conf_v == "highmem"]), col="blue", main=paste0("Highmem ", rownames(activityStatsHighmem)[1], "-", rownames(activityStatsHighmem)[length(activityStatsHighmem[,1])]))
        barplot(activityStatsGpu$Used, ylim=c(0,70), names.arg=names(cluster_conf_v[cluster_conf_v == "gpu"]), col="magenta", main=paste0("GPU ", rownames(activityStatsGpu)[1], "-", rownames(activityStatsGpu)[length(activityStatsGpu[,1])]))

        coreusage <- t(statslist$user[,2:4]); colnames(coreusage) <- statslist$user$User
        barplot(coreusage, ylim=c(0, max(colSums(coreusage))), names.arg=statslist$user$User, col=c("gold", "orange", "green", "blue"), main="Number of CPU Cores Occupied by Users")
        legend("topright", legend=c("Intel", "Short", "Batch", "Highmem"), cex=1.5, bty="n", pch=15, pt.cex=1.5, col=c("gold", "orange", "green", "blue"))
        
        barplot(t(statslist$waiting), ylim=c(0, (max(statslist$waiting)+1)), col=c(2,7,4,3,1,4,5,6,8), main="Recent Job History")
        legend("topright", legend=colnames(statslist$waiting), cex=1, bty="n", pch=15, pt.cex=1, col=c(2,7,4,3,1,4,5,6,8))
        
        if(all(is.na(statslist$user$GB_RAM))) statslist$user$GB_RAM <- 0
        barplot(statslist$user$GB_RAM, ylim=c(0, (max(statslist$user$GB_RAM, na.rm=TRUE)+1)), names.arg=statslist$user$User, col="yellow", main="GB RAM Explicitly Reserved by Users")
        
        mtext(paste("Activity Report Generated by jobMonitor on", format(Sys.time(), "%a, %b %d, %Y, at %H:%M:%S")), side = 3, line = -2, outer = TRUE, cex=1.3, font=2)

        if (margins == TRUE) { dev.off() }
    }

	if(plot=="pdf") {
        tmpfile <- paste("/tmp/jobMonitor", paste(sample(0:9, 6), collapse=""), ".pdf", sep="")
        pdf(tmpfile, height=10, width=16, bg="white")
		#x11(height=10, width=16, pointsize=12)
        configGraph()
	    system(paste("xpdf", tmpfile))
	}
    if(plot=="png") {
        png("/opt/linux/centos/7.x/x86_64/pkgs/hpcc_user_utils/jobMonitor/jobMonitor.png", height=1200, width=1100, pointsize=14)
        configGraph()
        #configGraph(margins=FALSE)
	}
	# Remove tmp PDF file if created
	if(1==length(list.files(pattern=tmpfile))) {
		unlink(tmpfile)
	}
	return(statslist)
}

options(width=220)
args = commandArgs(trailingOnly=TRUE)
if (length(args)==0){
    statslist <- statsReport(refresh=TRUE, plot="png", stdout=FALSE)
} else if (length(args)==1) {
    if (args[1]=="png" || args[1]=="pdf") {
        statslist <- statsReport(refresh=TRUE, plot=args[1], stdout=TRUE)
    } else {
        stop("Invalid format: type of plot must be png or pdf", call.=FALSE)
    }
} else {
    stop("Only one argument must be supplied: type of plot (ie. png, pdf)", call.=FALSE)
}

