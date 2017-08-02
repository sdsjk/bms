var Tabs = function(wrap, opts) {
        if(!(this instanceof Tabs)){
            return new Tabs(wrap, opts);
        }
        this.option = $.extend({
            tabs : '.slider-thumbnail li',
            views : '.slider-focus li',
            nextBtn : '.slider-btnnext',
            prevBtn : '.slider-btnprev',
            evtType : 'mouseover',
	        onTabChange : $.noop,
            tabClass : 'now',
            showIndex : 0,
            loop : false,
            autoPlay : true,
            interval : 2*1000
        },opts);
        var $wrap = $(wrap);
        var opts = this.option;
        var tabs = $wrap.find(opts.tabs);
        var views = $wrap.find(opts.views);
        if (!tabs.length || tabs.length != views.length) {
            //alert('tabs的元素为空或者tabs和views的元素个数不相等');
            return;
        }
        var self = this;
        var $self = $(self);
        var tabLength = tabs.length;
        var timer;
        tabs.each(function(num, val){
            if(!views[num]) return false;
            if(num != opts.showIndex){
                $(views[num]).css('display', 'none');
            }else{
                $(views[num]).css('display', 'block');
            }
            $(val).attr('jsvalue',num);
        });
        this.current = opts.showIndex;
        this.changeTab = function(ix) {
            ix = parseInt(ix);
            if(ix < 0 || ix > tabLength || isNaN(ix)) return;
            $(views[self.current]).css('display', 'none');
            $(tabs[self.current]).removeClass(opts.tabClass);
            self.current = ix;
            $(views[self.current]).css('display', 'block');
            $(tabs[self.current]).addClass(opts.tabClass);
	        opts.onTabChange(ix, tabs[self.current], tabs[ix]);
            $self.trigger('tabChange', [ix, tabs[self.current], tabs[ix]]);
        };
        this.next = function(){
            if(self.current < tabs.length - 1){
                self.changeTab(self.current + 1);
            }else{
                opts.loop ? self.changeTab(0) : $self.trigger('error',[1]);
            }
        };
        this.prev = function(){
            if(self.current > 0){
                self.changeTab(self.current - 1);
            }else{
                opts.loop ? self.changeTab(tabs.length) : $self.trigger('error',[0]);
            }
        };
        this.play = function(interval){
            interval = opts.interval = interval || opts.interval;
            if(interval < 1000) return;
            self.playing = true;
            bindHover();
            timer && clearTimeout(timer);
            timer = setTimeout(function(){
                timer = setTimeout(arguments.callee,interval);
                self.next();
            },interval);
        };
        this.stop = function(){
            self.playing = false;
            timer && clearTimeout(timer);
        };
        //绑定相关事件。
        function bind(){
            var cTimer;
            $wrap.delegate(opts.tabs, opts.evtType, function(evt) {
                var ix = $(evt.currentTarget).attr('jsvalue');
                if(!ix && ix != 0){
                    return;
                }
                ix = parseInt(ix);
                cTimer&&clearTimeout(cTimer);
                cTimer = setTimeout(function(){
                    self.changeTab(ix);
                }, 200);
            });
            $wrap.delegate(opts.nextBtn,'click',function(evt){
                self.next();
            });
            $wrap.delegate(opts.prevBtn,'click',function(evt){
                self.prev();
            });
            $self.bind('error',function(){
                self.stop();
            })
        }
        function bindHover(){
            $wrap.data('hover')||$wrap.hover(function(){
                self.stop();
            },function(){
                self.play();
            }).data('hover',true);
        }
        bind();
        this.changeTab(opts.showIndex);
        if(opts.autoPlay){
            this.play();
            bindHover();
        }
    };