function test() {

        var __temp_i = pairs.__iter__();
        try {
            while (true) {
                var temp_i = __temp_i.next();
                
                var i = temp_i.__getitem__(0);
                
                var j = temp_i.__getitem__(1);
                
        

            }
        } catch (e) {
            if (e != StopIteration) {
                throw e;
            }
        }
        
}


