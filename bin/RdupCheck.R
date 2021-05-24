#!/usr/bin/env Rscript

libPaths <- .libPaths()
libPath1 <- libPaths[[1]]
libPath2 <- libPaths[[2]]

cat(paste('\tComparing:',libPath1,libPath2,sep='\n'))

pkgs <- rownames(installed.packages(lib.loc=libPath1))
pkgs2 <- rownames(installed.packages(lib.loc=libPath2))
dups <- pkgs[pkgs %in% pkgs2]

if ( length(dups) > 0 ){
  cat("\n\n\tDuplicates found:\n")
  cat(paste(dups,collapse='\n'))
  
  cat("\n\nDelete duplicates from the following location: ")
  cat('\n\t',libPath1,"\n[N/y]: ")
  delPkgs <- readLines("stdin",n=1);
  if ( delPkgs == 'y' || delPkgs == 'Y' ){
      cat("\n\tDuplicates deleted\n")
  } else {
      cat("\n\tNOT deleting\n")
  }
}
