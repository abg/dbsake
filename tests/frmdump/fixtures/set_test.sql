CREATE TABLE `set_test` (
  `a` set('a','b','c') DEFAULT 'a',
  `b` set('a','b','c','d','e','f','g','h','i') DEFAULT 'a,h,i',
  `c` set('a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w') DEFAULT 'a,n,o,t,v,w',
  `d` set('0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r') DEFAULT '0,c,k,n,o,r',
  `e` set('0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','@','+') CHARACTER SET latin1 COLLATE latin1_general_cs DEFAULT '0,f,h,n,t,w,M,@'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
